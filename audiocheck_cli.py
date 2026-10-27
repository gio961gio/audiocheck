"""Command Line Interface (CLI) for AudioCheck.

Enables headless execution for audio engineering pipelines, mastering CI/CD,
and automated batch quality control.

Exit codes:
    0: PASS - All files passed quality control
    1: WARN - Quality control warnings present, no failures or errors
    2: FAIL - One or more files failed quality control limits
    3: ERROR - Decode error, missing files, or invalid input arguments
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path, PurePosixPath
import sys
import zipfile

from audiocheck_core import QCSettings
from engine.runner import BatchRunner
from profiles import BUILT_IN_PROFILES, settings_from_payload
from reporting import build_html_report

AUDIO_EXTENSIONS = {".wav", ".wave", ".flac", ".aif", ".aiff", ".ogg", ".mp3", ".m4a", ".mp4", ".wma"}

PRESET_SHORTCUTS = {
    "podcast": "Podcast & Streaming (AES TD1004 / Spotify / Apple)",
    "broadcast": "Broadcast TV & Radio (EBU R128)",
    "acx": "Audiobook (ACX / Audible Standard)",
    "audible": "Audiobook (ACX / Audible Standard)",
    "music": "Music Streaming (Mastering Target)",
    "generic": "General Purpose / Custom QC",
}


def collect_local_files(paths: list[str]) -> tuple[list[tuple[str, Path | bytes]], list[str]]:
    """Collect audio files from file paths, directories, and ZIP archives.

    Uses lazy Path references for local files to prevent loading gigabytes into RAM at once.
    """
    items: list[tuple[str, Path | bytes]] = []
    errors: list[str] = []

    for path_str in paths:
        p = Path(path_str)
        if not p.exists():
            errors.append(f"Path not found: {path_str}")
            continue

        if p.is_dir():
            for child in sorted(p.rglob("*")):
                if child.is_file() and child.suffix.lower() in AUDIO_EXTENSIONS:
                    try:
                        rel_path = child.relative_to(p).as_posix()
                        items.append((f"{p.name}/{rel_path}", child))
                    except Exception as exc:
                        errors.append(f"{child}: {exc}")
        elif p.suffix.lower() == ".zip":
            try:
                with zipfile.ZipFile(p) as archive:
                    for info in archive.infolist():
                        if info.is_dir():
                            continue
                        safe_path = PurePosixPath(info.filename)
                        if safe_path.suffix.lower() in AUDIO_EXTENSIONS:
                            try:
                                items.append((f"{p.name}/{safe_path.as_posix()}", archive.read(info)))
                            except Exception as exc:
                                errors.append(f"{p.name} -> {info.filename}: {exc}")
            except Exception as exc:
                errors.append(f"{p}: invalid ZIP archive ({exc})")
        elif p.suffix.lower() in AUDIO_EXTENSIONS:
            items.append((p.name, p))
        else:
            errors.append(f"Unsupported format or ignored file: {p.name}")

    return items, errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="audiocheck",
        description="AudioCheck CLI — Batch audio quality control engine for mastering, podcast, and broadcast.",
    )
    parser.add_argument(
        "inputs", nargs="*", help="Audio files, directories, or ZIP archives to analyze."
    )
    parser.add_argument(
        "--preset",
        choices=list(PRESET_SHORTCUTS.keys()),
        default="podcast",
        help="Standard compliance preset (podcast, broadcast, acx, music, generic). Default: podcast.",
    )
    parser.add_argument(
        "--profile",
        type=str,
        help="Path to custom QC profile in JSON format.",
    )
    parser.add_argument(
        "--target-lufs",
        type=float,
        help="Override target integrated loudness (LUFS).",
    )
    parser.add_argument(
        "--true-peak",
        type=float,
        help="Override maximum true peak ceiling (dBTP).",
    )
    parser.add_argument(
        "--out-dir", "-o",
        type=str,
        default=".",
        help="Directory to save exported reports (default: current directory).",
    )
    parser.add_argument(
        "--format",
        type=str,
        default=None,
        help="Report export formats to write to disk (html, json, csv). Default: html,json,csv (disabled in pure --json mode unless explicitly specified).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output complete analysis payload as JSON to stdout (optimized for automated CI/CD pipelines).",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Maximum parallel worker threads for batch processing.",
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress console progress bar and metric summary tables.",
    )

    args = parser.parse_args(argv)

    if not args.inputs:
        parser.print_help()
        return 3

    # Resolve settings and profile name
    profile_name = PRESET_SHORTCUTS.get(args.preset, "Podcast & Streaming (AES TD1004 / Spotify / Apple)")
    if args.profile:
        prof_path = Path(args.profile)
        if not prof_path.exists():
            sys.stderr.write(f"Error: QC profile file not found: {args.profile}\n")
            return 3
        try:
            payload = json.loads(prof_path.read_text(encoding="utf-8"))
            profile_name, settings = settings_from_payload(payload)
        except Exception as exc:
            sys.stderr.write(f"Error loading JSON profile: {exc}\n")
            return 3
    else:
        settings_dict = BUILT_IN_PROFILES[profile_name]["settings"]
        settings = QCSettings(**settings_dict)

    # Apply manual CLI overrides
    if args.target_lufs is not None:
        settings.target_lufs = float(args.target_lufs)
    if args.true_peak is not None:
        settings.true_peak_ceiling_dbtp = float(args.true_peak)

    if not args.quiet and not args.json:
        print("=" * 68)
        print("         AUDIOCHECK — BATCH AUDIO QUALITY CONTROL ENGINE")
        print("=" * 68)
        print(f"Active Profile : {profile_name}")
        print(f"Target Loudness: {settings.target_lufs:.1f} LUFS (±{settings.lufs_tolerance:.1f} LU)")
        print(f"True Peak Max  : {settings.true_peak_ceiling_dbtp:.1f} dBTP (ITU-R BS.1770-4 4x FIR)")
        print(f"LRA Max        : {settings.max_lra_lu:.1f} LU")
        print("=" * 68)

    files, collection_errors = collect_local_files(args.inputs)
    if collection_errors and not args.quiet and not args.json:
        for err in collection_errors:
            sys.stderr.write(f"[WARNING] {err}\n")

    if not files:
        sys.stderr.write("No valid audio files found in specified inputs.\n")
        return 3

    runner = BatchRunner(max_workers=args.workers, prefer_threads=True)

    def cli_progress(done: int, total: int, filename: str) -> None:
        if not args.quiet and not args.json:
            pct = int(done / total * 100)
            sys.stdout.write(f"\r[{done}/{total}] ({pct:3d}%) Analyzing: {filename[:35]:<35}")
            sys.stdout.flush()

    results, failures = runner.run(files, settings, progress_callback=cli_progress)

    if not args.quiet and not args.json:
        sys.stdout.write("\n")

    # Determine exit code with strict CI/CD semantics
    has_runtime_errors = bool(failures) or bool(collection_errors)
    has_qc_fails = any(r.get("status") == "FAIL" for r in results)
    has_qc_warns = any(r.get("status") == "WARN" for r in results)

    if has_runtime_errors:
        exit_code = 3  # Runtime / decode / missing files error
    elif has_qc_fails:
        exit_code = 2  # Quality control failure
    elif has_qc_warns:
        exit_code = 1  # Quality control warning
    else:
        exit_code = 0  # PASS

    # Console Summary Table
    if not args.json and not args.quiet:
        print("\n" + "-" * 75)
        print(f"{'STATUS':<6} | {'FILE':<28} | {'LUFS':<8} | {'TRUE PEAK':<10} | {'LRA':<6} | {'CORR':<5}")
        print("-" * 75)
        for r in results:
            st = r.get("status", "WARN")
            name = str(r.get("filename", ""))[:28]

            lufs_val = r.get("integrated_lufs")
            lufs_str = f"{lufs_val:.1f}" if lufs_val is not None else "N/A"

            tp_val = r.get("estimated_true_peak_dbtp")
            tp_str = f"{tp_val:.2f}" if tp_val is not None else "N/A"

            lra_val = r.get("loudness_range_lu")
            lra_str = f"{lra_val:.1f}" if lra_val is not None else "N/A"

            corr_val = r.get("stereo_correlation_avg")
            channels = r.get("channels", 1)
            if channels < 2:
                corr_str = "Mono"
            elif corr_val is not None:
                corr_str = f"{corr_val:.2f}"
            else:
                corr_str = "N/A"

            print(f"{st:<6} | {name:<28} | {lufs_str:<8} | {tp_str:<10} | {lra_str:<6} | {corr_str:<5}")

        for fail in failures:
            fail_name = str(fail.get("filename", "Unknown"))[:28]
            print(f"{'ERROR':<6} | {fail_name:<28} | {'N/A':<8} | {'N/A':<10} | {'N/A':<6} | {'N/A':<5}")

        print("-" * 75)
        count_p = sum(r.get("status") == "PASS" for r in results)
        count_w = sum(r.get("status") == "WARN" for r in results)
        count_f = sum(r.get("status") == "FAIL" for r in results)
        count_e = len(failures) + len(collection_errors)
        total_eval = len(results) + len(failures)
        print(f"SUMMARY: {total_eval} evaluated · PASS: {count_p} · WARN: {count_w} · FAIL: {count_f} · ERROR: {count_e}")
        status_label = "PASS" if exit_code == 0 else ("WARN" if exit_code == 1 else ("FAIL" if exit_code == 2 else "ERROR"))
        print(f"OVERALL OUTCOME: {status_label} (Exit code: {exit_code})")

    # Output generation
    if args.format is not None:
        requested_formats = [f.strip().lower() for f in args.format.split(",") if f.strip()]
    elif args.json:
        # Pure stdout stream: do not create files on disk by default
        requested_formats = []
    else:
        requested_formats = ["html", "json", "csv"]

    out_dir = Path(args.out_dir)
    if requested_formats:
        out_dir.mkdir(parents=True, exist_ok=True)

    json_payload = {
        "profile_name": profile_name,
        "exit_code": exit_code,
        "settings": settings.to_dict(),
        "summary": {
            "total_files": len(results) + len(failures),
            "pass_count": sum(r.get("status") == "PASS" for r in results),
            "warn_count": sum(r.get("status") == "WARN" for r in results),
            "fail_count": sum(r.get("status") == "FAIL" for r in results),
            "error_count": len(failures) + len(collection_errors),
        },
        "results": results,
        "failures": failures,
        "collection_errors": collection_errors,
    }

    if args.json:
        print(json.dumps(json_payload, indent=2, ensure_ascii=False))

    if "json" in requested_formats:
        json_path = out_dir / "audiocheck_report.json"
        json_path.write_text(json.dumps(json_payload, indent=2, ensure_ascii=False), encoding="utf-8")
        if not args.quiet and not args.json:
            print(f"[OK] JSON report saved to: {json_path}")

    if "html" in requested_formats:
        html_report = build_html_report(results, failures, settings.to_dict(), profile_name, collection_errors)
        html_path = out_dir / "audiocheck_report.html"
        html_path.write_text(html_report, encoding="utf-8")
        if not args.quiet and not args.json:
            print(f"[OK] HTML report saved to: {html_path}")

    if "csv" in requested_formats:
        fieldnames = [
            "Status", "Filename", "Duration (s)", "Sample Rate (Hz)", "Channels",
            "Integrated LUFS", "LRA (LU)", "True Peak (dBTP)", "Sample Peak (dBFS)",
            "Crest Factor (dB)", "Stereo Correlation", "Mono Drop (dB)",
            "Flat-top Clipping (samples)", "Leading Silence (s)", "Trailing Silence (s)",
            "Error Details",
        ]
        csv_path = out_dir / "audiocheck_report.csv"
        with open(csv_path, mode="w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for r in results:
                writer.writerow({
                    "Status": r.get("status"),
                    "Filename": r.get("filename"),
                    "Duration (s)": r.get("duration_s"),
                    "Sample Rate (Hz)": r.get("sample_rate_hz"),
                    "Channels": r.get("channels"),
                    "Integrated LUFS": r.get("integrated_lufs"),
                    "LRA (LU)": r.get("loudness_range_lu"),
                    "True Peak (dBTP)": r.get("estimated_true_peak_dbtp"),
                    "Sample Peak (dBFS)": r.get("sample_peak_dbfs"),
                    "Crest Factor (dB)": r.get("crest_factor_db"),
                    "Stereo Correlation": r.get("stereo_correlation_avg"),
                    "Mono Drop (dB)": r.get("mono_drop_db"),
                    "Flat-top Clipping (samples)": r.get("flat_top_samples"),
                    "Leading Silence (s)": r.get("leading_silence_s"),
                    "Trailing Silence (s)": r.get("trailing_silence_s"),
                    "Error Details": "",
                })
            for fail in failures:
                writer.writerow({
                    "Status": "ERROR",
                    "Filename": fail.get("filename", ""),
                    "Error Details": fail.get("error", ""),
                })
        if not args.quiet and not args.json:
            print(f"[OK] CSV report saved to: {csv_path}")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
