from __future__ import annotations

from io import BytesIO
import json
from pathlib import PurePosixPath
import re
import zipfile

import pandas as pd
import streamlit as st

from audiocheck_core import QCSettings, analyze_audio
from engine.runner import BatchRunner
from profiles import BUILT_IN_PROFILES, profile_json, settings_from_payload
from reporting import build_html_report, _render_meter_bars, get_remediation_advice

st.set_page_config(page_title="AudioCheck", page_icon="🎚️", layout="wide")

# Styling: Taste Skill (Anti-Slop Minimalist Studio Theme)
st.markdown("""
<style>
/* Clean typography and tabular numbers */
html, body, [class*="css"] {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}
div[data-testid="stMetricValue"] {
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace !important;
    font-feature-settings: "tnum" !important;
}
/* Visual meter cards inside Streamlit */
.meter-box {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 14px 18px;
    margin: 10px 0 16px 0;
}
.meter-row {
    display: flex;
    align-items: center;
    gap: 14px;
    margin-bottom: 8px;
    font-size: 13px;
}
.meter-label {
    width: 150px;
    font-weight: 600;
    color: #e6edf3;
    font-size: 12px;
}
.meter-bar-track {
    flex: 1;
    height: 12px;
    background: #21262d;
    border-radius: 6px;
    position: relative;
    overflow: hidden;
}
.meter-bar-fill {
    height: 100%;
    border-radius: 6px;
    transition: width 0.3s ease;
}
.meter-target-zone {
    position: absolute;
    top: 0;
    bottom: 0;
    background: rgba(16, 185, 129, 0.25);
    border-left: 1px dashed #10b981;
    border-right: 1px dashed #10b981;
}
.meter-marker {
    position: absolute;
    top: 0;
    bottom: 0;
    width: 2px;
    background: #ef4444;
    z-index: 2;
}
.phase-track .meter-center-marker {
    position: absolute;
    top: 0;
    bottom: 0;
    left: 50%;
    width: 2px;
    background: #8b949e;
    z-index: 1;
}
.meter-val {
    width: 100px;
    text-align: right;
    font-weight: 700;
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    font-size: 12px;
}
.remediation-box {
    background: #1c1917;
    border-left: 4px solid #f59e0b;
    padding: 12px 16px;
    margin-top: 14px;
    border-radius: 0 8px 8px 0;
    font-size: 12px;
    color: #f5f5f4;
    line-height: 1.6;
}
</style>
""", unsafe_allow_html=True)

AUDIO_EXTENSIONS = {".wav", ".wave", ".flac", ".aif", ".aiff", ".ogg", ".mp3", ".m4a", ".mp4", ".wma"}
MAX_FILE_BYTES = 100 * 1024 * 1024
MAX_TOTAL_BYTES = 500 * 1024 * 1024


def profile_key(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    return slug[:40] or "qc"


def collect_audio_files(uploaded_files):
    """Collect supported audio payloads without extracting ZIP paths to disk."""
    items = []
    errors = []
    total_bytes = 0
    for upload in uploaded_files or []:
        data = upload.getvalue()
        lower_name = upload.name.lower()
        if len(data) > MAX_TOTAL_BYTES:
            errors.append(f"{upload.name}: upload exceeds 500 MB limit, ignored.")
            continue
        if lower_name.endswith(".zip"):
            try:
                with zipfile.ZipFile(BytesIO(data)) as archive:
                    for info in archive.infolist():
                        if info.is_dir():
                            continue
                        safe_path = PurePosixPath(info.filename)
                        if safe_path.suffix.lower() not in AUDIO_EXTENSIONS:
                            continue
                        if info.file_size > MAX_FILE_BYTES:
                            errors.append(f"{upload.name} → {info.filename}: individual file exceeds 100 MB, ignored.")
                            continue
                        if total_bytes + info.file_size > MAX_TOTAL_BYTES:
                            errors.append("Overall batch limit of 500 MB reached; remaining files ignored.")
                            return items, errors
                        with archive.open(info) as f:
                            audio_data = f.read(MAX_FILE_BYTES + 1)
                        if len(audio_data) > MAX_FILE_BYTES:
                            errors.append(f"{upload.name} → {info.filename}: individual file exceeds 100 MB, ignored.")
                            continue
                        total_bytes += len(audio_data)
                        items.append((f"{upload.name} / {safe_path.as_posix()}", audio_data))
            except zipfile.BadZipFile:
                errors.append(f"{upload.name}: invalid ZIP archive.")
        else:
            if len(data) > MAX_FILE_BYTES:
                errors.append(f"{upload.name}: individual file exceeds 100 MB, ignored.")
                continue
            if total_bytes + len(data) > MAX_TOTAL_BYTES:
                errors.append("Overall batch limit of 500 MB reached; remaining files ignored.")
                return items, errors
            total_bytes += len(data)
            items.append((upload.name, data))
    return items, errors


if "imported_profile" not in st.session_state:
    st.session_state["imported_profile"] = None
if "profile_select" not in st.session_state:
    st.session_state["profile_select"] = "Podcast & Streaming (AES TD1004 / Spotify / Apple)"

st.title("🎚️ AudioCheck")
st.caption("Professional Batch Audio Quality Control & Loudness Compliance Engine · Music Engineering Portfolio Project")
st.write(
    "Automated metrological QC inspection for podcasts, voiceover, commercial music, and broadcast distribution. "
    "All processing runs locally in memory conforming to ITU-R BS.1770-4, EBU R128, and AES TD1004 recommendations."
)

with st.sidebar:
    st.header("QC Profile")
    profile_upload = st.file_uploader("Import JSON Profile", type=["json"], key="profile_json_upload")
    if st.button("Import Profile", disabled=profile_upload is None, use_container_width=True):
        try:
            payload = json.loads(profile_upload.getvalue().decode("utf-8"))
            imported_name, imported_settings = settings_from_payload(payload)
            st.session_state["imported_profile"] = {
                "profile_name": imported_name,
                "settings": imported_settings.to_dict(),
            }
            st.session_state["profile_select"] = "Imported Profile"
            st.session_state.pop("active_profile_token", None)
            st.rerun()
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
            st.error(f"Failed to import profile: {exc}")

    profile_options = list(BUILT_IN_PROFILES)
    if st.session_state.get("imported_profile"):
        profile_options.append("Imported Profile")
    if st.session_state.get("profile_select") not in profile_options:
        st.session_state["profile_select"] = profile_options[0]
    selected_profile = st.selectbox("Compliance Preset", options=profile_options, key="profile_select")

    if selected_profile == "Imported Profile":
        profile_data = st.session_state["imported_profile"]
        base_settings = profile_data["settings"]
        displayed_profile_name = profile_data["profile_name"]
    else:
        profile_data = BUILT_IN_PROFILES[selected_profile]
        base_settings = profile_data["settings"]
        displayed_profile_name = selected_profile
        st.caption(profile_data["description"])

    prefix = "imported" if selected_profile == "Imported Profile" else profile_key(selected_profile)
    profile_token = f"{selected_profile}:{json.dumps(base_settings, sort_keys=True)}"
    if st.session_state.get("active_profile_token") != profile_token:
        for field_name, field_value in base_settings.items():
            st.session_state[f"qc_{prefix}_{field_name}"] = field_value
        st.session_state["active_profile_token"] = profile_token

    st.caption("Configurable Thresholds: Customize parameters to match specific platform or client delivery guidelines.")
    target_lufs = st.number_input(
        "Target Loudness (LUFS)", -36.0, 0.0, step=0.5,
        key=f"qc_{prefix}_target_lufs",
    )
    lufs_tolerance = st.number_input(
        "Loudness Tolerance (± LU)", 0.0, 12.0, step=0.5,
        key=f"qc_{prefix}_lufs_tolerance",
    )
    true_peak_ceiling = st.number_input(
        "True Peak Ceiling (dBTP)", -12.0, 3.0, step=0.5,
        key=f"qc_{prefix}_true_peak_ceiling_dbtp",
    )
    max_edge_silence = st.number_input(
        "Max Edge Silence per Boundary (s)", 0.0, 30.0, step=0.25,
        key=f"qc_{prefix}_max_edge_silence_s",
    )
    dc_limit = st.number_input(
        "DC Offset Limit (dBFS)", -120.0, 0.0, step=5.0,
        key=f"qc_{prefix}_dc_offset_limit_dbfs",
    )
    silence_threshold = st.number_input(
        "Silence Gate Threshold (dBFS)", -100.0, -10.0, step=5.0,
        key=f"qc_{prefix}_silence_threshold_dbfs",
    )
    min_silence_region = st.number_input(
        "Min Silence Region Duration (s)", 0.01, 30.0, step=0.05,
        key=f"qc_{prefix}_min_silence_region_s",
    )
    oversampling_factor = st.select_slider(
        "True Peak Oversampling Factor (BS.1770 FIR)",
        options=[1, 2, 4, 8, 16],
        key=f"qc_{prefix}_oversampling_factor",
    )
    clipping_threshold = st.number_input(
        "Near Full-Scale Threshold", 0.5, 1.0, step=0.001,
        format="%.3f", key=f"qc_{prefix}_clipping_threshold",
    )
    max_lra = st.number_input(
        "Max Loudness Range (LRA in LU)", 1.0, 50.0, step=0.5,
        key=f"qc_{prefix}_max_lra_lu",
    )
    min_phase_corr = st.number_input(
        "Min Stereo Phase Correlation", -1.0, 1.0, step=0.05,
        key=f"qc_{prefix}_min_phase_correlation",
    )
    max_mono_drop = st.number_input(
        "Max Mono Fold-Down Attenuation (dB)", 0.0, 60.0, step=0.5,
        key=f"qc_{prefix}_max_mono_drop_db",
    )

    settings = QCSettings(
        target_lufs=float(target_lufs),
        lufs_tolerance=float(lufs_tolerance),
        true_peak_ceiling_dbtp=float(true_peak_ceiling),
        max_edge_silence_s=float(max_edge_silence),
        dc_offset_limit_dbfs=float(dc_limit),
        silence_threshold_dbfs=float(silence_threshold),
        min_silence_region_s=float(min_silence_region),
        oversampling_factor=int(oversampling_factor),
        clipping_threshold=float(clipping_threshold),
        max_lra_lu=float(max_lra),
        min_phase_correlation=float(min_phase_corr),
        max_mono_drop_db=float(max_mono_drop),
    )
    st.download_button(
        "Export Active Profile (.json)",
        data=profile_json(displayed_profile_name, settings),
        file_name=f"{profile_key(displayed_profile_name)}_profile.json",
        mime="application/json",
        use_container_width=True,
    )
    st.divider()
    st.caption("Note: True peak is computed via ITU-R BS.1770-4 48-tap polyphase interpolation; edge silence uses RMS window gating.")

st.subheader("1 · Select Audio Files")
uploads = st.file_uploader(
    "Upload audio files or ZIP archive containing stems",
    type=["wav", "wave", "flac", "aif", "aiff", "ogg", "mp3", "m4a", "mp4", "wma", "zip"],
    accept_multiple_files=True,
    key="audio_files_upload",
    help="Uncompressed WAV and FLAC recommended. Compressed formats (MP3/AAC/OGG) supported via FFmpeg.",
)
if st.button("Analyze Audio Stems", type="primary", disabled=not uploads, use_container_width=True):
    files, collection_errors = collect_audio_files(uploads)
    st.session_state["audio_collection_errors"] = collection_errors
    st.session_state["audio_results"] = []
    st.session_state["audio_failures"] = []
    st.session_state["audio_settings"] = settings.to_dict()
    st.session_state["audio_profile_name"] = displayed_profile_name
    results = []
    failures = []
    progress = st.progress(0, text="Initializing metrological analysis…")
    if not files:
        progress.empty()
        st.error("No valid audio files found. Please upload audio files or a ZIP archive containing audio.")
    else:
        runner = BatchRunner(prefer_threads=True)
        def on_progress(done: int, total: int, current_name: str) -> None:
            short_name = current_name.split("/")[-1].strip()[:30]
            progress.progress(done / total, text=f"Analyzed {done} of {total} files ({short_name})...")
        results, failures = runner.run(files, settings, progress_callback=on_progress)
        progress.empty()
        st.session_state["audio_results"] = results
        st.session_state["audio_failures"] = failures

for message in st.session_state.get("audio_collection_errors", []):
    st.warning(message)

results = st.session_state.get("audio_results", [])
failures = st.session_state.get("audio_failures", [])
if results or failures:
    st.subheader("2 · Batch Metric Summary")
    count_pass = sum(r["status"] == "PASS" for r in results)
    count_warn = sum(r["status"] == "WARN" for r in results)
    count_fail = sum(r["status"] == "FAIL" for r in results)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Files Evaluated", len(results))
    c2.metric("PASS", count_pass)
    c3.metric("WARN", count_warn)
    c4.metric("FAIL", count_fail + len(failures))

    table_rows = []
    for result in results:
        table_rows.append({
            "Status": result["status"],
            "Filename": result["filename"],
            "Duration (s)": result["duration_s"],
            "Sample Rate (Hz)": result["sample_rate_hz"],
            "Channels": result["channels"],
            "Integrated LUFS": result["integrated_lufs"],
            "LRA (LU)": result["loudness_range_lu"],
            "True Peak (dBTP)": result["estimated_true_peak_dbtp"],
            "Sample Peak (dBFS)": result["sample_peak_dbfs"],
            "Crest Factor (dB)": result.get("crest_factor_db"),
            "Stereo Correlation": result.get("stereo_correlation_avg"),
            "Mono Drop (dB)": result.get("mono_drop_db"),
            "Flat-top Clipping (samples)": result.get("flat_top_samples", 0),
            "Leading Silence (s)": result["leading_silence_s"],
            "Trailing Silence (s)": result["trailing_silence_s"],
        })
    df = pd.DataFrame(table_rows)
    st.dataframe(df, use_container_width=True, hide_index=True)

    csv_data = df.to_csv(index=False).encode("utf-8-sig")
    st.download_button("Download CSV Summary", data=csv_data, file_name="audiocheck_report.csv", mime="text/csv")
    report_settings = st.session_state.get("audio_settings", settings.to_dict())
    report_profile = st.session_state.get("audio_profile_name", displayed_profile_name)
    report_errors = st.session_state.get("audio_collection_errors", [])
    json_data = json.dumps({
        "profile_name": report_profile,
        "settings": report_settings,
        "results": results,
        "decode_failures": failures,
        "collection_errors": report_errors,
    }, ensure_ascii=False, indent=2).encode("utf-8")
    st.download_button("Download JSON Report", data=json_data, file_name="audiocheck_report.json", mime="application/json")
    html_report = build_html_report(results, failures, report_settings, report_profile, report_errors)
    st.download_button("Download Professional HTML Report", data=html_report.encode("utf-8"), file_name="audiocheck_report.html", mime="text/html")

    st.subheader("3 · Detailed Metric Evaluation")
    for result in results:
        with st.expander(f"{result['status']} · {result['filename']}"):
            # 1. Visual Meter Bars (ITU-R BS.1770-4 & Stereo Correlation)
            meters_html = _render_meter_bars(result, settings.to_dict())
            if meters_html:
                st.markdown(f"<div class='meter-box'>{meters_html}</div>", unsafe_allow_html=True)

            # 2. Checks Table
            st.dataframe(pd.DataFrame(result["checks"]), use_container_width=True, hide_index=True)

            # 3. DAW Remediation Advice
            remediation_items = []
            for check in result.get("checks", []):
                st_val = check.get("status")
                if st_val in ("WARN", "FAIL"):
                    adv = get_remediation_advice(check.get("check", ""), st_val, check.get("value", ""), check.get("detail", ""))
                    if adv:
                        remediation_items.append(f"<li><strong>{check.get('check', '')} [{st_val}]:</strong> {adv}</li>")
            if remediation_items:
                st.markdown(
                    f"""<div class="remediation-box">
                        <h4 style="margin:0 0 6px; color:#f59e0b; font-size:13px;">🛠️ DAW Remediation Guide (Reaper / Pro Tools / Logic / Audition)</h4>
                        <ul style="margin:0; padding-left:18px;">{''.join(remediation_items)}</ul>
                    </div>""",
                    unsafe_allow_html=True,
                )

            st.write(f"Total silence detected: **{result['total_detected_silence_s']:.2f} s**")
            if result["silence_regions"]:
                st.caption("Gated silence intervals (RMS threshold). Does not indicate unintended pauses.")
                st.dataframe(pd.DataFrame(result["silence_regions"]), use_container_width=True, hide_index=True)
    if failures:
        st.subheader("Unprocessed Files / Errors")
        st.dataframe(pd.DataFrame(failures), use_container_width=True, hide_index=True)

with st.expander("Metrics, Measurement Methods & Engineering Standards"):
    st.markdown(
        """
        - **Integrated Loudness**: Calibrated via ITU-R BS.1770-4 / EBU R128 with K-weighting pre-filter and dual gating (relative -10 LU, absolute -70 LUFS).
        - **True Peak**: 48-tap polyphase FIR filter (4x/8x oversampling) detecting inter-sample peaks prior to D/A conversion.
        - **Digital Flat-Top Clipping**: Tracks consecutive saturation events at $\\ge 0.999$ full scale (length $N \\ge 3$).
        - **Stereo Phase Correlation**: Pearson correlation coefficient $[-1.0, +1.0]$ across audio blocks with mono fold-down attenuation check.
        - **Edge Silence**: Sub-millisecond boundary analysis for head and tail lead-in/lead-out compliance (ACX, podcast distributors).
        - **Privacy & Security**: All DSP operations execute in-memory on the local host with zero external network telemetry.
        """
    )

st.divider()
st.caption("AudioCheck · Authored by Giovanni Antonecchia · Music Engineering, Politecnico di Milano")
