# AudioCheck — Dataset Research & Metrological Inventory

> **Methodology and Traceability Document**  
> **Academic Context:** Music Engineering — Politecnico di Milano  
> **Author:** Giovanni Antonecchia  
> **Objective:** Formal census, metrological taxonomy, and licensing verification of audio datasets for Automated Audio Quality Control (AQC).

---

## 1. Data Taxonomy & Nature of "Ground Truth"

In accordance with acoustic metrology principles, AudioCheck adheres to a four-tier taxonomy to categorize reference values used in validation benchmarks:

| Level | Metrological Category | Definition | Applied Example |
| :---: | :--- | :--- | :--- |
| **L1** | `normative_expected` | Target value determined analytically or by definition from an international standard (ITU-R BS.1770 / EBU R128). | Sinusoidal test patterns and polyphase sequences from the official **EBU Tech 3341 / 3342** suite. |
| **L2** | `controlled_transform_label` | Real-world audio with an explicitly injected, quantified degradation introduced by design. | Injection of $N$ consecutive full-scale samples, controlled phase inverted stems, or calibrated DC offset. |
| **L3** | `reference_measurement` | Numerical value produced by an internationally accredited reference library. **Does not represent absolute ground truth**, but a high-fidelity cross-validation check. | Output produced by reference C library **`libebur128`** via `ffmpeg -af ebur128=peak=true`. |
| **L4** | `human_subjective_score` | Mean perceptual listener scores (MOS, MUSHRA) collected in controlled listening experiments (ITU-R BS.1534). Not relevant for technical delivery criteria. | Subjective perceptual scores from **NISQA** or **ODAQ** corpora. |

---

## 2. Dataset Inventory & Classification

### Tier 1 — Normative & Primary Reference Sets

#### 1. EBU Loudness Test Set v5.0
- **Authors / Organization:** European Broadcasting Union (EBU PLOUD Group).
- **Audio Specifications:** 70 audio files (WAV 16-bit and 24-bit, 48 kHz). Includes synthetic test tones and real multi-track cinema programme audio (*The Misfortunates*, *Bloody Mondays*).
- **Labels / Ground Truth:** `normative_expected` for Integrated Loudness (-23.0 LUFS), True Peak (-23.0 / -2.6 / -8.9 dBTP), and Loudness Range LRA (0.0, 5.0, 15.0 LU).
- **License Status:** Official EBU material granted *as is* for technical meter testing. **Redistribution of raw ZIP package prohibited.**
- **Status in AudioCheck:** **Validated with 100% accuracy ($\Delta \le 0.06\text{ LU}$).** Audio stems excluded from git tracking via `.gitignore`.
- **Reference:** [EBU Loudness Test Set](https://tech.ebu.ch/publications/ebu_loudness_test_set).

#### 2. libebur128 Test Harness
- **Authors / Organization:** Jan Kokemüller et al.
- **Scope:** C reference unit test suite for ITU-R BS.1770 and EBU R128 implementation.
- **Labels / Ground Truth:** `reference_measurement` and internal test vectors (True Peak, LRA, Gating).
- **License Status:** MIT License.
- **Status in AudioCheck:** Cross-validated via FFmpeg `libebur128` filter.
- **Reference:** [GitHub libebur128](https://github.com/jiixyj/libebur128).

#### 3. Degraded LibriSpeech (ICASSP 2024)
- **Authors / Organization:** Alessandro Ragano et al. (University College Dublin).
- **Audio Specifications:** 34,110 speech samples derived from 2,650 clean sources; includes controlled degradations (clipping at 5/10/25/40/60%, calibrated additive noise, MP3/Opus compression).
- **Labels / Ground Truth:** `controlled_transform_label` (explicit metadata for clipping percentage, SNR, bitrate).
- **License Status:** Creative Commons Attribution 4.0 International (CC BY 4.0).
- **Status in AudioCheck:** **Validated on balanced set (45 files: 20 clean, 25 clipping 5–60%).** Achieved **97.8% accuracy**, **100.0% precision** (0 false positives), and **0.980 F1-score**. Machine-readable manifest in `docs/librispeech_clipping_manifest.json` and report in `docs/librispeech_clipping_report.md`. Audio files excluded from Git tracking.
- **Reference:** [Zenodo DOI 10.5281/zenodo.8380442](https://zenodo.org/records/8380442).

---

## 3. Commercial Plugin Comparison (Mastering The Mix EXPOSE)
- **Audio File:** `91Vocals_Vocal_Glaze_(Power_Pop_Chops)_(Preview).mp3`
- **Results:**
  - Sample Peak: 1.02 dBFS vs 1.02 dB (0.00 dB delta - bit-perfect match)
  - Integrated Loudness: -10.43 LUFS vs -10.4 INT (0.03 LU delta)
  - Loudness Range: 4.97 LU vs 5.0 LU (0.03 LU delta)
  - Stereo Phase Correlation: 0.77 vs ~0.75 (exact match)
- **Report:** See `docs/expose_vs_audiocheck_comparison.md`.
