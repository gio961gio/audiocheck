"""Accuracy Evaluation and Performance Benchmark for AudioCheck.

Evaluates AudioCheck against the calibrated Ground Truth dataset (EBU Tech 3341,
EBU Tech 3342, ITU-R BS.1770-4), measuring metric delta errors, SHA256 provenance,
and processing speed according to the metrological brief.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import sys
import time

from audiocheck_core import QCSettings
from engine.runner import BatchRunner


def compute_file_sha256(path: Path) -> str:
    """Compute cryptographic SHA-256 digest of an audio file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def run_benchmark() -> dict:
    root = Path(__file__).resolve().parent.parent
    dataset_dir = root / "datasets" / "ebu_compliance"
    gt_path = dataset_dir / "ground_truth.json"

    if not gt_path.exists():
        from scripts.generate_ground_truth_dataset import generate_dataset
        generate_dataset()

    catalog = json.loads(gt_path.read_text(encoding="utf-8"))
    files_to_test = []
    file_hashes = {}

    for fname in sorted(catalog.keys()):
        p = dataset_dir / fname
        if p.exists():
            files_to_test.append((fname, p))
            file_hashes[fname] = compute_file_sha256(p)

    if not files_to_test:
        print("Errore: nessun file audio trovato nel dataset.")
        sys.exit(1)

    settings = QCSettings(
        target_lufs=-23.0,
        lufs_tolerance=0.5,
        true_peak_ceiling_dbtp=-1.0,
        oversampling_factor=4,
    )

    runner = BatchRunner(max_workers=4, prefer_threads=True)

    start_time = time.perf_counter()
    results, failures = runner.run(files_to_test, settings)
    elapsed_s = time.perf_counter() - start_time

    results_by_name = {r["filename"]: r for r in results}

    metric_evaluations = []
    total_audio_duration_s = 0.0

    for fname, meta in catalog.items():
        res = results_by_name.get(fname)
        expected_metrics = meta.get("metrics", {})
        total_audio_duration_s += meta.get("duration_s", 0.0)
        sha256_hash = file_hashes.get(fname, "N/D")
        gt_type = meta.get("ground_truth_type", "normative_expected")
        ref_method = meta.get("reference_method", "ITU-R BS.1770-4 / EBU Tech 3341")

        for m_name, m_spec in expected_metrics.items():
            target = m_spec["target"]
            tol = m_spec["tolerance"]
            unit = m_spec.get("unit", "")

            if res is None:
                passed = False
                measured = None
                delta = None
            else:
                measured = res.get(m_name)
                if measured is None:
                    passed = False
                    delta = None
                else:
                    delta = abs(float(measured) - float(target))
                    passed = delta <= tol

            metric_evaluations.append({
                "file": fname,
                "audio_sha256": sha256_hash,
                "description": meta.get("description", ""),
                "ground_truth_type": gt_type,
                "reference_method": ref_method,
                "metric": m_name,
                "target": target,
                "measured": measured,
                "tolerance": tol,
                "delta": delta,
                "unit": unit,
                "passed": passed,
            })

    total_checks = len(metric_evaluations)
    passed_checks = sum(1 for m in metric_evaluations if m["passed"])
    accuracy_pct = (passed_checks / total_checks * 100.0) if total_checks else 0.0
    speed_factor = (total_audio_duration_s / elapsed_s) if elapsed_s > 0 else 0.0

    summary = {
        "audiocheck_version": "2.0.0",
        "benchmark_date": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "total_files": len(files_to_test),
        "total_checks": total_checks,
        "passed_checks": passed_checks,
        "failed_checks": total_checks - passed_checks,
        "accuracy_pct": accuracy_pct,
        "total_audio_duration_s": total_audio_duration_s,
        "elapsed_s": elapsed_s,
        "speed_factor_realtime": speed_factor,
        "evaluations": metric_evaluations,
        "failures": failures,
    }

    # Console output
    print("=" * 90)
    print("      AUDIOCHECK — GROUND TRUTH ACCURACY & PERFORMANCE SCORECARD")
    print("=" * 90)
    print(f"File analizzati      : {len(files_to_test)} file")
    print(f"Durata audio totale  : {total_audio_duration_s:.2f} s ({total_audio_duration_s / 60.0:.2f} min)")
    print(f"Tempo di calcolo     : {elapsed_s:.3f} s")
    print(f"Velocità throughput  : {speed_factor:.1f}x Real-Time")
    print(f"Verifiche metriche   : {passed_checks}/{total_checks} superate")
    print(f"ACCURATEZZA GLOBALE  : {accuracy_pct:.1f}%")
    print("=" * 90)
    print(f"{'STATUS':<6} | {'FILE':<28} | {'METRICA':<20} | {'TARGET':<10} | {'MISURATO':<10} | {'DELTA':<7} | {'GT TYPE':<16}")
    print("-" * 90)

    for item in metric_evaluations:
        st_mark = "PASS" if item["passed"] else "FAIL"
        fname_short = item["file"][:28]
        m_name = item["metric"][:20]
        tgt_str = f"{item['target']}{item['unit']}"
        val_str = f"{item['measured']:.2f}{item['unit']}" if isinstance(item["measured"], (int, float)) else "N/D"
        delta_str = f"{item['delta']:.3f}" if isinstance(item["delta"], (int, float)) else "N/D"
        gt_type_str = item["ground_truth_type"][:16]
        print(f"{st_mark:<6} | {fname_short:<28} | {m_name:<20} | {tgt_str:<10} | {val_str:<10} | {delta_str:<7} | {gt_type_str:<16}")

    print("-" * 90)

    docs_dir = root / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)

    # Save structured JSON manifest
    manifest_path = docs_dir / "accuracy_manifest.json"
    manifest_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[OK] Manifest JSON salvato in: {manifest_path}")

    # Generate Markdown Report
    md_lines = [
        "# AudioCheck — Rapporto Scientifico di Accuratezza e Benchmark DSP",
        "",
        "> **Protocollo Metrologico:** Validazione deterministica rispetto alle specifiche analitiche e ai segnali di prova delle raccomandazioni internazionali **ITU-R BS.1770-4**, **EBU Tech 3341** ed **EBU Tech 3342**.",
        "",
        "## 1. Indicatori Chiave di Prestazione (KPI)",
        "",
        f"- **Versione AudioCheck:** `{summary['audiocheck_version']}`",
        f"- **Data Benchmark:** {summary['benchmark_date']}",
        f"- **Accuratezza Globale del Modello:** **{accuracy_pct:.1f}%** ({passed_checks}/{total_checks} controlli conformi)",
        f"- **Throughput Computazionale:** **{speed_factor:.1f}× Real-Time**",
        f"- **Durata Audio Elaborata:** {total_audio_duration_s:.2f} secondi ({total_audio_duration_s / 60.0:.2f} minuti)",
        f"- **Tempo di Elaborazione su CPU:** {elapsed_s:.3f} secondi",
        "",
        "## 2. Matrice di Validazione Ground Truth vs AudioCheck",
        "",
        "| Esito | File di Test | SHA-256 (Primi 8 car.) | Metrica DSP | Target Ground Truth | Valore Rilevato | Errore Delta ($\\Delta$) | Tolleranza Ammessa | Categoria GT |",
        "| :---: | :--- | :---: | :--- | :---: | :---: | :---: | :---: | :--- |",
    ]

    for item in metric_evaluations:
        icon = "✅ PASS" if item["passed"] else "❌ FAIL"
        sha_short = item["audio_sha256"][:8]
        tgt = f"{item['target']} {item['unit']}"
        meas = f"{item['measured']:.2f} {item['unit']}" if isinstance(item["measured"], (int, float)) else "N/D"
        delta = f"{item['delta']:.4f}" if isinstance(item["delta"], (int, float)) else "N/D"
        tol = f"±{item['tolerance']} {item['unit']}"
        gt_t = item["ground_truth_type"]
        md_lines.append(f"| {icon} | `{item['file']}` | `{sha_short}` | **{item['metric']}** | {tgt} | {meas} | {delta} | {tol} | `{gt_t}` |")

    report_md_path = docs_dir / "accuracy_benchmark_report.md"
    report_md_path.write_text("\n".join(md_lines), encoding="utf-8")
    print(f"[OK] Report scientifico salvato in: {report_md_path}")

    return summary


if __name__ == "__main__":
    run_benchmark()
