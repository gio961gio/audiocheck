"""Self-contained HTML report generation for AudioCheck."""
from __future__ import annotations

from datetime import datetime, timezone
from html import escape
import math
from typing import Any


STATUS_LABELS = {"PASS": "PASS", "WARN": "WARN", "FAIL": "FAIL"}


def _e(value: Any) -> str:
    return escape(str(value if value is not None else "N/D"), quote=True)


def _fmt(value: Any, suffix: str = "") -> str:
    if value is None:
        return "N/D"
    if isinstance(value, (int, float)):
        return f"{value:g}{suffix}"
    return f"{value}{suffix}"


def get_remediation_advice(check_name: str, status: str, value: Any, detail: str) -> str:
    """Provide professional audio engineering guidance for issues flagged during QC."""
    if status == "PASS":
        return ""

    check_lower = check_name.lower()
    if "integrated loudness" in check_lower or "loudness integrato" in check_lower:
        return (
            "Adjust output gain or limiter threshold on the master bus to match the delivery target. "
            "In Reaper, Pro Tools, Logic, or Audition, use an ITU-R BS.1770 / EBU R128 compliant meter "
            "(e.g., Youlean, FabFilter Pro-L 2, WLM) to calibrate integrated loudness."
        )
    elif "momentary" in check_lower or "momentanea" in check_lower or "short-term" in check_lower:
        return (
            "Short-term loudness peaks exceed the prescribed threshold. "
            "Use a fast-response peak limiter/compressor on transients (fast attack, 50-100 ms release) "
            "or apply Clip Gain / Volume Automation on high-energy passages."
        )
    elif "true peak" in check_lower or "picco" in check_lower:
        return (
            "Enable True Peak Limiting (with 4x or 8x inter-sample oversampling) on your final master limiter. "
            "Set the ceiling to -1.0 dBTP (or -2.0 dBTP for lossy MP3/AAC distribution) to prevent inter-sample clipping during D/A conversion."
        )
    elif "phase" in check_lower or "fase" in check_lower or "correlation" in check_lower or "correlazione" in check_lower or "mono" in check_lower:
        return (
            "Critical stereo correlation or phase cancellation detected in mono downmix. Narrow stereo wideners on "
            "low frequencies (sum to mono below 150 Hz). If correlation is negative, check mic alignment or invert polarity (Ø) on one channel."
        )
    elif "clip" in check_lower or "flat-top" in check_lower:
        return (
            "Consecutive flat full-scale samples detected. Reduce pre-gain to prevent digital bus clipping. "
            "If distortion occurred during tracking, apply a de-clip module (e.g., iZotope RX) to reconstruct waveform peaks."
        )
    elif "silence" in check_lower or "silenzio" in check_lower:
        return (
            "Perform a 'Top and Tail' edit in your DAW timeline: trim excess leading/trailing silence to conform with "
            "platform specifications and apply 5-10 ms micro-fades to avoid boundary clicks."
        )
    elif "dc offset" in check_lower:
        return (
            "Engage a high-pass filter (15-20 Hz, 18-24 dB/oct) on the master chain to eliminate DC bias and recover digital headroom."
        )
    elif "lra" in check_lower or "dynamics" in check_lower or "dinamica" in check_lower:
        return (
            "Loudness dynamic range exceeds target bounds. "
            "Apply gentle bus compression (1.5:1 or 2:1 ratio) or volume automation across wide dynamic sections."
        )
    elif "sample rate" in check_lower or "frequency" in check_lower or "frequenza" in check_lower or "channels" in check_lower or "canali" in check_lower:
        return (
            "Sample rate or channel layout mismatch with profile specifications. "
            "Re-render/bounce from your DAW with target parameters using a quality band-limited sinc resampler."
        )
    return "Inspect master bus levels and processing chain for the flagged parameter."


def _render_meter_bars(result: dict[str, Any], settings: dict[str, Any]) -> str:
    """Generate visual meter indicators for LUFS, True Peak, and Phase Correlation.

    Protected against NaN, inf, and digital silence. Uses bipolar expansion for stereo phase.
    """
    bars_html = []

    # 1. Loudness bar (-36 to 0 LUFS) with dynamic target zone
    lufs = result.get("integrated_lufs")
    target = float(settings.get("target_lufs", -16.0))
    tol = float(settings.get("lufs_tolerance", 2.0))
    if lufs is not None and math.isfinite(float(lufs)):
        lufs_float = float(lufs)
        lufs_clamped = max(-36.0, min(0.0, lufs_float))
        pct = (lufs_clamped + 36.0) / 36.0 * 100.0
        delta = abs(lufs_float - target)
        color = "#10b981" if delta <= tol else ("#ef4444" if delta > tol * 1.5 else "#f59e0b")
        target_pct = (max(-36.0, min(0.0, target)) + 36.0) / 36.0 * 100.0
        zone_width_pct = min(100.0, (tol * 2.0) / 36.0 * 100.0)
        zone_left_pct = max(0.0, min(100.0 - zone_width_pct, target_pct - (zone_width_pct / 2.0)))
        bars_html.append(f"""
        <div class="meter-row">
            <span class="meter-label">Loudness (LUFS)</span>
            <div class="meter-bar-track">
                <div class="meter-target-zone" style="left:{zone_left_pct:.1f}%; width:{zone_width_pct:.1f}%;"></div>
                <div class="meter-bar-fill" style="width:{pct:.1f}%; background:{color};"></div>
            </div>
            <span class="meter-val" style="color:{color};">{lufs_float:.1f} LUFS</span>
        </div>
        """)

    # 2. True Peak bar (-24 to +3 dBTP)
    tp = result.get("estimated_true_peak_dbtp")
    tp_ceiling = float(settings.get("true_peak_ceiling_dbtp", -1.0))
    if tp is not None and math.isfinite(float(tp)):
        tp_float = float(tp)
        tp_clamped = max(-24.0, min(3.0, tp_float))
        pct = (tp_clamped + 24.0) / 27.0 * 100.0
        color = "#ef4444" if tp_float > tp_ceiling else "#10b981"
        ceil_pct = (max(-24.0, min(3.0, tp_ceiling)) + 24.0) / 27.0 * 100.0
        bars_html.append(f"""
        <div class="meter-row">
            <span class="meter-label">True Peak (dBTP)</span>
            <div class="meter-bar-track">
                <div class="meter-marker" style="left:{ceil_pct:.1f}%;" title="Ceiling: {tp_ceiling:.1f} dBTP"></div>
                <div class="meter-bar-fill" style="width:{pct:.1f}%; background:{color};"></div>
            </div>
            <span class="meter-val" style="color:{color};">{tp_float:.2f} dBTP</span>
        </div>
        """)

    # 3. Stereo Correlation (-1.0 to +1.0) — Professional bipolar representation from center (0.0)
    corr = result.get("stereo_correlation_avg")
    channels = result.get("channels", 1)
    min_corr = float(settings.get("min_phase_correlation", 0.0))
    if channels >= 2 and corr is not None and math.isfinite(float(corr)):
        corr_float = float(corr)
        corr_clamped = max(-1.0, min(1.0, corr_float))

        # Color aligned to configured profile threshold
        if corr_float < min_corr:
            color = "#ef4444"
        elif corr_float < min_corr + 0.3:
            color = "#f59e0b"
        else:
            color = "#10b981"

        if corr_clamped >= 0.0:
            bar_left = 50.0
            bar_width = corr_clamped * 50.0
        else:
            bar_left = 50.0 + (corr_clamped * 50.0)
            bar_width = abs(corr_clamped) * 50.0

        bars_html.append(f"""
        <div class="meter-row">
            <span class="meter-label">Correlazione Fase</span>
            <div class="meter-bar-track phase-track">
                <div class="meter-center-marker"></div>
                <div class="meter-bar-fill" style="position:absolute; left:{bar_left:.1f}%; width:{bar_width:.1f}%; background:{color};"></div>
            </div>
            <span class="meter-val" style="color:{color};">{corr_float:.2f}</span>
        </div>
        """)

    if not bars_html:
        return ""

    joined_bars = "".join(bars_html)
    return f"""
    <div class="meter-box">
        <h4 style="margin:0 0 10px; font-size:13px; color:var(--muted); text-transform:uppercase; letter-spacing:0.04em;">Indicatori Visivi di Controllo</h4>
        {joined_bars}
    </div>
    """


def build_html_report(
    results: list[dict[str, Any]],
    failures: list[dict[str, str]],
    settings: dict[str, Any],
    profile_name: str,
    collection_errors: list[str] | None = None,
    generated_at: str | None = None,
) -> str:
    """Create an offline-friendly HTML report. All user-controlled text is escaped."""
    generated_at = generated_at or datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    counts = {status: sum(item.get("status") == status for item in results) for status in STATUS_LABELS}
    overall = "FAIL" if counts["FAIL"] or failures else ("WARN" if counts["WARN"] else "PASS")
    collection_errors = collection_errors or []

    summary_rows = []
    for result in results:
        corr_val = result.get("stereo_correlation_avg")
        if corr_val is not None and math.isfinite(float(corr_val)) and result.get("channels", 1) >= 2:
            corr_str = f"{float(corr_val):.2f}"
        elif result.get("channels", 1) < 2:
            corr_str = "Mono"
        else:
            corr_str = "N/D"

        lra_str = _fmt(result.get("loudness_range_lu"), " LU")
        crest_str = _fmt(result.get("crest_factor_db"), " dB")
        summary_rows.append(
            "<tr>"
            f"<td><span class='badge {_e(result.get('status', 'WARN'))}'>{_e(result.get('status', 'WARN'))}</span></td>"
            f"<td class='filename'>{_e(result.get('filename'))}</td>"
            f"<td>{_fmt(result.get('duration_s'), ' s')}</td>"
            f"<td>{_fmt(result.get('sample_rate_hz'), ' Hz')}</td>"
            f"<td>{_fmt(result.get('channels'))}</td>"
            f"<td>{_fmt(result.get('integrated_lufs'), ' LUFS')}</td>"
            f"<td>{lra_str}</td>"
            f"<td>{_fmt(result.get('estimated_true_peak_dbtp'), ' dBTP')}</td>"
            f"<td>{_fmt(result.get('sample_peak_dbfs'), ' dBFS')}</td>"
            f"<td>{crest_str}</td>"
            f"<td>{corr_str}</td>"
            f"<td>{_fmt(result.get('leading_silence_s'), ' / ' + _fmt(result.get('trailing_silence_s'), ' s'))}</td>"
            "</tr>"
        )

    detail_sections = []
    for result in results:
        check_rows = []
        remediation_items = []

        for check in result.get("checks", []):
            status = check.get("status", "WARN")
            name = check.get("check", "")
            val = check.get("value", "")
            det = check.get("detail", "")

            check_rows.append(
                "<tr>"
                f"<td><span class='badge {_e(status)}'>{_e(status)}</span></td>"
                f"<td>{_e(name)}</td>"
                f"<td>{_e(val)}</td>"
                f"<td>{_e(det)}</td>"
                "</tr>"
            )

            if status in ("WARN", "FAIL"):
                adv = get_remediation_advice(name, status, val, det)
                if adv:
                    remediation_items.append(
                        f"<li><strong>{_e(name)} [{_e(status)}]:</strong> {_e(adv)}</li>"
                    )

        tbody_html = "".join(check_rows) if check_rows else "<tr><td colspan='4'>No checks available</td></tr>"
        meters_html = _render_meter_bars(result, settings)

        if remediation_items:
            remediation_html = f"""
            <div class="remediation-box">
                <h4 style="margin:0 0 6px; color:#b45309; font-size:13px;">🛠️ DAW Remediation Guide (Reaper / Pro Tools / Logic / Audition)</h4>
                <ul style="margin:0; padding-left:18px;">{''.join(remediation_items)}</ul>
            </div>
            """
        else:
            remediation_html = """
            <div class="remediation-box pass">
                <strong style="color:#065f46;">✓ All metrics pass quality control. No DAW adjustments required.</strong>
            </div>
            """

        detail_sections.append(
            f"<section class='file-detail'><h3>{_e(result.get('filename'))} "
            f"<span class='badge {_e(result.get('status', 'WARN'))}'>{_e(result.get('status', 'WARN'))}</span></h3>"
            f"{meters_html}"
            "<table><thead><tr><th>Status</th><th>Check</th><th>Value</th><th>Details / Threshold</th></tr></thead>"
            f"<tbody>{tbody_html}</tbody></table>"
            f"{remediation_html}"
            f"<p class='muted'>Total Detected Silence: {_fmt(result.get('total_detected_silence_s'), ' s')} · "
            f"DC Offset: {_fmt(result.get('dc_offset_dbfs'), ' dBFS')} · "
            f"Digital Flat-Top Samples (N≥3): {_fmt(result.get('flat_top_samples'), ' samples')}.</p>"
            "</section>"
        )

    warning_blocks = [f"<li>{_e(message)}</li>" for message in collection_errors]
    for item in failures:
        warning_blocks.append(f"<li>{_e(item.get('filename'))}: {_e(item.get('error'))}</li>")

    settings_rows = []
    labels = {
        "target_lufs": "Target Loudness (LUFS)",
        "lufs_tolerance": "Loudness Tolerance (LU)",
        "true_peak_ceiling_dbtp": "Estimated True Peak Ceiling (dBTP)",
        "max_lra_lu": "Max Loudness Range (LRA in LU)",
        "max_momentary_lufs": "Max Momentary Loudness (LUFS)",
        "max_short_term_lufs": "Max Short-Term Loudness (LUFS)",
        "min_phase_correlation": "Min Stereo Phase Correlation",
        "max_mono_drop_db": "Max Mono Fold-Down Attenuation (dB)",
        "max_flat_top_samples": "Flat-Top Clipping Sample Tolerance",
        "max_edge_silence_s": "Max Boundary Silence per Edge (s)",
        "dc_offset_limit_dbfs": "DC Offset Limit (dBFS)",
        "silence_threshold_dbfs": "Silence Threshold (dBFS)",
        "min_silence_region_s": "Min Silence Region Duration (s)",
        "clipping_threshold": "Full-Scale Sample Threshold",
        "oversampling_factor": "Oversampling Factor (ITU-R BS.1770-4)",
    }
    for key, label in labels.items():
        if key in settings:
            settings_rows.append(f"<tr><td>{_e(label)}</td><td>{_e(settings[key])}</td></tr>")

    summary_tbody = "".join(summary_rows) if summary_rows else "<tr><td colspan='12'>No files analyzed</td></tr>"
    detail_html = "".join(detail_sections) if detail_sections else "<p class='muted'>No file details available.</p>"
    warning_section = f"<section class='panel'><h2>Unprocessed Files / Warnings</h2><ul>{''.join(warning_blocks)}</ul></section>" if warning_blocks else ""

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AudioCheck — Professional QC Report</title>
<style>
:root {{ color-scheme: light; --ink:#19202b; --muted:#667085; --line:#e5e7eb; --bg:#f7f8fa; }}
* {{ box-sizing: border-box; }}
body {{ margin:0; font:14px/1.5 Inter,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; color:var(--ink); background:var(--bg); }}
main {{ max-width:1500px; margin:0 auto; padding:32px 22px 56px; }}
header, .panel {{ background:#fff; border:1px solid var(--line); border-radius:14px; padding:22px; margin-bottom:18px; }}
h1 {{ margin:0 0 6px; font-size:28px; }}
h2 {{ font-size:19px; margin:0 0 14px; }}
h3 {{ font-size:15px; margin:0 0 10px; overflow-wrap:anywhere; }}
.muted {{ color:var(--muted); }}
.metrics {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:10px; margin-top:18px; }}
.metric {{ border:1px solid var(--line); border-radius:10px; padding:12px; }}
.metric strong {{ display:block; font-size:25px; }}
.badge {{ display:inline-block; border-radius:6px; padding:2px 7px; font-size:11px; font-weight:700; letter-spacing:.03em; }}
.PASS {{ color:#17663a; background:#e7f6ec; }}
.WARN {{ color:#855600; background:#fff2d2; }}
.FAIL {{ color:#9b2020; background:#fde8e8; }}
table {{ width:100%; border-collapse:collapse; font-size:12px; }}
th, td {{ border-bottom:1px solid var(--line); padding:9px 10px; text-align:left; vertical-align:top; }}
th {{ background:#f6f7f9; white-space:nowrap; }}
td {{ overflow-wrap:anywhere; }}
.table-wrap {{ overflow-x:auto; }}
.filename {{ min-width:180px; max-width:330px; overflow-wrap:anywhere; }}
.file-detail {{ border-top:1px solid var(--line); padding-top:16px; margin-top:20px; }}
.meter-box {{ background:#f8fafc; border:1px solid var(--line); border-radius:10px; padding:14px; margin:14px 0; }}
.meter-row {{ display:flex; align-items:center; gap:12px; margin-bottom:8px; font-size:12px; }}
.meter-label {{ width:140px; font-weight:600; color:var(--ink); }}
.meter-bar-track {{ flex:1; height:12px; background:#e2e8f0; border-radius:6px; position:relative; overflow:hidden; }}
.meter-bar-fill {{ height:100%; border-radius:6px; transition:width .3s ease; }}
.meter-target-zone {{ position:absolute; top:0; bottom:0; background:rgba(16,185,129,0.25); border-left:1px dashed #10b981; border-right:1px dashed #10b981; }}
.meter-marker {{ position:absolute; top:0; bottom:0; width:2px; background:#ef4444; z-index:2; }}
.phase-track .meter-center-marker {{ position:absolute; top:0; bottom:0; left:50%; width:2px; background:#94a3b8; z-index:1; }}
.meter-val {{ width:95px; text-align:right; font-weight:700; font-family:ui-monospace,Menlo,monospace; font-size:12px; }}
.remediation-box {{ background:#fffbeb; border-left:4px solid #f59e0b; padding:12px 16px; margin-top:14px; border-radius:0 8px 8px 0; font-size:12px; line-height:1.6; }}
.remediation-box.pass {{ background:#ecfdf5; border-left-color:#10b981; }}
footer {{ color:var(--muted); font-size:12px; margin-top:20px; }}
@media(max-width:800px) {{ .metrics {{ grid-template-columns:repeat(2,minmax(0,1fr)); }} main {{ padding:14px; }} }}
@media print {{
    body {{ background:#fff; }}
    main {{ max-width:none; padding:0; }}
    header, .panel {{ break-inside:avoid; border-color:#ccc; }}
    .file-detail {{ break-inside:avoid; }}
    .badge, .meter-bar-fill, .meter-target-zone {{ print-color-adjust: exact; -webkit-print-color-adjust: exact; }}
}}
</style>
</head>
<body>
<main>
<header>
    <p class="muted">AUDIOCHECK · PROFESSIONAL AUDIO QUALITY CONTROL REPORT</p>
    <h1>Batch Audio Quality Control Report</h1>
    <p class="muted">Profile: <strong>{_e(profile_name)}</strong> · Generated: {_e(generated_at)}</p>
    <div class="metrics">
        <div class="metric"><span class="muted">Overall Status</span><strong><span class="badge {overall}">{overall}</span></strong></div>
        <div class="metric"><span class="muted">Files Evaluated</span><strong>{len(results)}</strong></div>
        <div class="metric"><span class="muted">Passed (PASS)</span><strong>{counts['PASS']}</strong></div>
        <div class="metric"><span class="muted">Warnings / Fails</span><strong>{counts['WARN']} / {counts['FAIL'] + len(failures)}</strong></div>
    </div>
</header>
<section class="panel">
    <h2>Batch Files & Metric Summary</h2>
    <div class="table-wrap">
        <table>
            <thead>
                <tr>
                    <th>Status</th><th>Filename</th><th>Duration</th><th>Sample Rate</th><th>Channels</th>
                    <th>Loudness</th><th>LRA</th><th>True Peak (BS.1770)</th><th>Sample Peak</th>
                    <th>Crest Factor</th><th>Correlation</th><th>Edge Silence (Head / Tail)</th>
                </tr>
            </thead>
            <tbody>{summary_tbody}</tbody>
        </table>
    </div>
</section>
<section class="panel">
    <h2>File Analysis Details</h2>
    {detail_html}
</section>
<section class="panel">
    <h2>QC Profile Specifications</h2>
    <div class="table-wrap">
        <table>
            <thead><tr><th>Control Parameter</th><th>Target / Boundary Threshold</th></tr></thead>
            <tbody>{''.join(settings_rows)}</tbody>
        </table>
    </div>
</section>
{warning_section}
<footer>
    <p>AudioCheck · Conforming to ITU-R BS.1770-4, EBU R128 and AES TD1004 engineering standards. True peak estimated via 4-phase 48-tap polyphase FIR filter; stereo phase check includes Pearson correlation and mono fold-down cancellation.</p>
    <p>To archive a PDF copy: Open in browser and select Print → Save as PDF.</p>
</footer>
</main>
</body>
</html>"""
