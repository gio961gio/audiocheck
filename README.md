# AudioCheck — Professional Audio Quality Control & Loudness Compliance Engine

[![CI](https://github.com/gio961gio/audiocheck/actions/workflows/ci.yml/badge.svg)](https://github.com/gio961gio/audiocheck/actions/workflows/ci.yml)
[![Python 3.10 | 3.11 | 3.12](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue)](https://www.python.org/)
[![License: Proprietary](https://img.shields.io/badge/License-Proprietary-red.svg)](LICENSE)
[![Standards: ITU--R BS.1770--4 | EBU R128 | AES TD1004](https://img.shields.io/badge/Standards-ITU--R%20BS.1770--4%20%7C%20EBU%20R128%20%7C%20AES%20TD1004-emerald)](#supported-audio-standards)
[![Live Demo](https://img.shields.io/badge/Streamlit_Cloud-Live_Demo-FF4B4B?logo=streamlit&logoColor=white)](https://audiocheck-engine.streamlit.app)

**AudioCheck** is an automated, broadcast-grade audio quality control (AQC) and metrological compliance engine. Engineered for post-production facilities, podcast networks, mastering engineers, and audio publishers (ACX / Audible), it validates multi-stem deliverables against international broadcast regulations and streaming distribution targets.

Developed by **Giovanni Antonecchia** (*Music Engineering, Politecnico di Milano*).

> [!NOTE]
> **Proprietary DSP Engine & Academic Evaluation**  
> AudioCheck's core DSP algorithms (ITU-R BS.1770-4 48-tap polyphase FIR filter, dual-stage EBU R128 loudness gating, and concurrent batch pipeline) are protected intellectual property.  
> 
> You can **test the engine live with your own audio files** via the **[Interactive Web Demo](https://audiocheck-engine.streamlit.app)** or request full source code access for institutional and academic evaluation by contacting [Giovanni Antonecchia](mailto:gio.antonecchia961@gmail.com).

---

## 📸 Visual Showcase & Interface

### 1. Minimalist Dark Studio Web Dashboard
Interactive local web application featuring real-time visual tolerance zones, True Peak ceilings, bipolar stereo phase correlation meters, and instant DAW remediation guidance.

![Dark Studio Dashboard](assets/studio_dashboard_dark.png)

---

### 2. Commercial Plugin Metrological Validation
Direct metrological cross-validation against **Mastering The Mix EXPOSE** and **FFmpeg `libebur128`** on commercial music audio (`91Vocals - Vocal Glaze Power Pop Chops`):

![EXPOSE vs AudioCheck Scorecard](assets/expose_vs_audiocheck_scorecard.png)

---

### 3. Headless Terminal CI/CD Execution
Command-line interface with deterministic exit codes (`0=PASS`, `1=WARN`, `2=FAIL`, `3=ERROR`) for automated mastering build and ingest pipelines:

![CLI Batch Showcase](assets/cli_batch_showcase.png)

---

### 4. Self-Contained Offline HTML Quality Control Report
Client-ready inspection reports with dynamic meter bars and DAW adjustment advice (Reaper, Pro Tools, Logic Pro, Audition):

![HTML Report Preview](assets/audiocheck_report_preview.png)

---

## 🏛️ System Architecture

AudioCheck is built on a decoupled, **local-first** architecture: the core DSP engine is completely independent of the presentation layers, enabling concurrent execution via thread or process pools with zero cloud dependency and strict in-memory security.

```mermaid
flowchart TD
    subgraph INPUT ["Audio Ingest & Sources"]
        A1["Uncompressed PCM (WAV / FLAC / AIFF)"]
        A2["Lossy Formats via FFmpeg (MP3 / AAC / OGG)"]
        A3["ZIP Packages (In-memory, Zip-Slip safe)"]
        A4["Recursive Directory Traversal"]
    end

    subgraph ENGINE ["DSP Core Engine (audiocheck_core.py)"]
        B1["Audio Decoder (SoundFile / FFmpeg Pipe)"]
        B2["True Peak 4x Polyphase FIR (ITU-R BS.1770-4 Annex 2)"]
        B3["Loudness Suite: LUFS, LRA (EBU Tech 3342), Momentary & Short-Term"]
        B4["Phase Correlation: Pearson r + Mono Fold-Down Attenuation dB"]
        B5["Digital Saturation: Flat-Top Clipping (N >= 3) & DC Offset"]
        B6["Sub-Millisecond Edge Silence Gating (5ms RMS / 1ms Hop)"]
    end

    subgraph RUNNER ["Concurrent Batch Runner (engine/runner.py)"]
        C1["ThreadPool & ProcessPool Worker Dispatch"]
        C2["Lazy Path Loading (Anti-RAM saturation)"]
    end

    subgraph INTERFACES ["Access Interfaces"]
        D1["Headless CLI (audiocheck_cli.py)"]
        D2["Dark Studio Web UI (Streamlit app.py)"]
    end

    subgraph OUTPUT ["Delivery & Reports"]
        E1["Self-Contained Offline HTML Report"]
        E2["Structured JSON & CSV Artifacts"]
        E3["Deterministic CI/CD Exit Codes"]
    end

    INPUT --> INTERFACES
    INTERFACES --> RUNNER
    RUNNER --> ENGINE
    ENGINE --> OUTPUT
```

---

## 🎯 Supported Standards & Compliance Presets

| Delivery Profile | Target Integrated Loudness | True Peak Ceiling | Max LRA | Edge Silence | Stereo Phase |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Podcast & Streaming** (AES TD1004 / Apple / Spotify) | **-16.0 LUFS** (±1.5 LU) | **-1.0 dBTP** | 12.0 LU | ≤ 2.0 s | $\rho \ge 0.1$ |
| **Broadcast TV & Radio** (EBU R128) | **-23.0 LUFS** (±0.5 LU) | **-1.0 dBTP** | 18.0 LU | ≤ 2.0 s | $\rho \ge 0.2$ |
| **Audiobook Delivery** (ACX / Audible Standard) | **-20.0 LUFS** (±2.0 LU) | **-3.0 dBTP** | 10.0 LU | ≤ 1.0 s | $\rho \ge 0.3$ |
| **Music Streaming** (Mastering Target) | **-14.0 LUFS** (±1.5 LU) | **-1.0 dBTP** | 16.0 LU | ≤ 3.0 s | $\rho \ge 0.0$ |
| **General Purpose QC** | Configurable | Configurable | Custom | Custom | Custom |

---

## 🔬 Metrological Benchmark Results

AudioCheck undergoes continuous validation against normative ground-truth corpora:

### 1. EBU Tech 3341 / 3342 Normative Test Suite
- Tested against the official European Broadcasting Union test set (`ebu-loudness-test-setv05`).
- **Result:** **100% test pass rate** with $\Delta \le 0.06$ LU on K-weighted integrated loudness, and exact +3.01 dB overshoot detection on $45^\circ$ inter-sample peak patterns.

### 2. Commercial Plugin Benchmark vs Mastering The Mix EXPOSE
- Audio File: `91Vocals - Vocal Glaze Power Pop Chops (Preview).mp3`
- **Sample Peak:** 1.02 dBFS vs 1.02 dB (**0.00 dB delta — bit-perfect match**).
- **Integrated Loudness:** -10.43 LUFS vs -10.4 INT (**0.03 LU delta — sub-perceptual**).
- **Loudness Range (LRA):** 4.97 LU vs 5.0 LU (**0.03 LU delta**).
- **Stereo Phase Correlation:** 0.77 vs ~0.75 (**exact match**).

### 3. Degraded LibriSpeech Dataset (ICASSP 2024 - Ragano et al.)
- Validated on 45 balanced human speech stems (clean dialogue and clipped recordings at 5% to 60% saturation).
- **Accuracy:** **97.8%**
- **Precision:** **100.0%** (Zero false alarms on dynamic, clean speech)
- **Recall:** **96.0%**
- **F1-Score:** **0.980**

---

## 🚀 Live Evaluation & Interactive Demo

The AudioCheck engine is hosted and ready for immediate online evaluation:

[![Open Live Demo](https://img.shields.io/badge/Launch-AudioCheck_Live_Demo-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://audiocheck-engine.streamlit.app)

### How to Evaluate:
1. Open the **[Live Interactive Web Demo](https://audiocheck-engine.streamlit.app)** in any desktop or mobile browser.
2. Drag and drop any uncompressed (.wav, .flac) or compressed (.mp3, .m4a) audio stems or ZIP packages.
3. Select an industry delivery preset (**EBU R128**, **AES TD1004 / Streaming**, **ACX / Audible**, or **Music Mastering**).
4. Inspect real-time metrological indicators (ITU-R BS.1770 True Peak, Pearson stereo phase correlation, LRA dynamics) and download the self-contained offline HTML inspection report with actionable DAW remediation advice.

---

## ⚙️ Headless CLI & Automated Pipeline Architecture

In addition to the interactive dashboard, AudioCheck includes a high-throughput headless CLI designed for automated mastering workflows, ingest servers, and CI/CD audio pipelines.

### Deterministic Exit Codes for CI/CD

| Exit Code | Classification | Operational Meaning |
| :---: | :---: | :--- |
| `0` | **PASS** | All evaluated stems strictly satisfy every normative threshold. |
| `1` | **WARN** | Minor acoustic warning (e.g., slight dynamic deviation or low DC offset). No hard failure. |
| `2` | **FAIL** | One or more audio files violated critical platform limits (true peak overshoot, clipping, loudness target). |
| `3` | **ERROR** | Corrupt/unreadable file header, missing stem, or invalid argument payload. |

### Output Artifacts
- **Structured JSON**: Machine-readable payload printed to `stdout` or disk for automated build pipelines.
- **CSV Summary**: Tabular audit log with loudness, dynamic range, and channel metrics for spreadsheet analysis.
- **Self-Contained HTML**: Executive report with embedded CSS styling and targeted DAW adjustment guidelines (Reaper, Pro Tools, Logic Pro, Audition).

---

## 🧪 Metrological Verification & Test Suite

The engine undergoes rigorous automated regression testing across 36 specialized test suites verifying algorithmic compliance against primary international standards:

- **ITU-R BS.1770-4 Annex 2**: Polyphase 48-tap FIR filter 4x inter-sample peak detection.
- **EBU Tech 3341 / 3342**: Dual-stage loudness gating (-70 LUFS / -10 LU) and statistical LRA percentiles.
- **ACX / Audible Requirements**: Boundary threshold compliance for loudness, true peak, and edge silence.
- **ICASSP 2024 Speech Degradation**: Waveform plateau analysis on clipped speech corpora.

```text
tests/test_accuracy_benchmarks.py::test_accuracy_ground_truth_suite PASSED
tests/test_acx_profile.py::test_acx_loudness_range_boundaries PASSED
tests/test_acx_profile.py::test_acx_true_peak_ceiling_boundary PASSED
tests/test_acx_profile.py::test_acx_edge_silence_boundary PASSED
tests/test_acx_profile.py::test_acx_dc_offset_boundary PASSED
tests/test_cli.py::test_cli_json_mode_pure_stdout_no_disk_side_effects PASSED
tests/test_core.py::test_ebu_tech_3341_inter_sample_peak_overshoot PASSED
tests/test_core.py::test_stereo_phase_correlation_and_mono_drop PASSED
tests/test_degraded_librispeech.py::test_degraded_librispeech_benchmark_execution PASSED
tests/test_profiles_reporting.py::test_html_report_renders_meter_bars_and_daw_remediation PASSED
tests/test_real_world_ebu.py::test_real_world_ebu_programme_simulation_accuracy PASSED
============================= 36 passed =============================
```

---

## 🔒 Source Code Access & Institutional Evaluation

The core DSP engine and CLI distribution are proprietary intellectual property of **Giovanni Antonecchia** (*Music Engineering, Politecnico di Milano*).

For institutional review, academic evaluation, or commercial deployment inquiries, please contact:  
📧 **[gio.antonecchia961@gmail.com](mailto:gio.antonecchia961@gmail.com)**

---

## 📄 License & Intellectual Property

Copyright © 2026 Giovanni Antonecchia. All rights reserved.  
The underlying AudioCheck DSP engine and algorithms are proprietary intellectual property. See the [LICENSE](LICENSE) file for evaluation terms.
