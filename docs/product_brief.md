# AudioCheck — Technical Product Brief & Engineering Showcase

> **Technical & Engineering Showcase Document**  
> *Target: Audio Software R&D Teams, Mastering Facilities, Broadcast Networks, Audio Publishing Houses.*  
> *Author: Giovanni Antonecchia (Music Engineering, Politecnico di Milano)*

---

## 1. Executive Summary

**AudioCheck** is an enterprise-grade automated audio quality control (AQC) and metrological compliance engine. It validates batch audio stems and deliverables against international broadcast standards, commercial streaming targets (Spotify, Apple Music), podcast distributors, and audiobook specifications (ACX / Audible).

The system bridges the gap between expensive proprietary broadcast hardware (e.g., TC Electronic, Dolby Media Producer, NUGEN Audio) and manual timeline inspection, delivering:
1. **A pure DSP metrological engine** conforming strictly to **ITU-R BS.1770-4 Annex 2**, **EBU R128**, and **EBU Tech 3342**.
2. **A headless CLI with strict CI/CD exit codes** (`0=PASS`, `1=WARN`, `2=FAIL`, `3=ERROR`) for automated build and render pipelines.
3. **An interactive local-first Dark Studio web dashboard** for instant visual inspection and interactive stem analysis.
4. **Self-contained offline client reports** featuring dynamic visual meters and **actionable DAW remediation guidance (Reaper, Pro Tools, Logic, Audition)**.

---

## 2. Industry Challenge: The Audio Quality Control Bottleneck

In modern digital audio distribution:
- **Platform Rejections:** ACX systematically rejects audiobooks exceeding -3.0 dBFS true peak or exhibiting background noise above -60 dBFS. Spotify and Apple Podcasts penalize unnormalized loudness and tracks with inter-sample peaks > -1.0 dBTP, which produce quantization and reconstruction distortion during AAC/MP3 lossy encoding.
- **Cost of Manual Verification:** Mastering engineers spend 15–20 minutes per 60-minute master opening files in a DAW, measuring integrated loudness, inspecting stereo phase coherence, checking boundary silence, and verifying true peaks.
- **Inter-Plugin Discrepancies:** Commercial limiters often use generic polynomial interpolation for true peak measurement, leading to false positives or undetected inter-sample clipping across diverse D/A converters.

---

## 3. Core DSP Architecture & Standard Conformance

AudioCheck implements rigorous DSP algorithms formulated according to primary scientific publications and international standards:

### A. True Peak: 4-Phase 48-Tap Polyphase FIR Interpolator (ITU-R BS.1770-4 Annex 2)
Generic tools often rely on standard spline or linear interpolation. AudioCheck implements the exact 48-tap polyphase FIR filter specified in Annex 2 of ITU-R BS.1770-4, partitioned into four 12-coefficient sub-phases for 4x oversampling:
$$\hat{x}[4n + p] = \sum_{k=0}^{11} h_p[k] \, x[n - k], \quad p \in \{0, 1, 2, 3\}$$
*Validation:* Accurately detects within 0.05 dBTP the +3.01 dB overshoot predicted by the official EBU Tech 3341 test pattern on $f_s/4$ sine waves sampled at $45^\circ$.

### B. Loudness Suite & Dynamic Range (EBU Tech 3342)
Complete psychoacoustic loudness analysis with K-weighting pre-filtering:
- **Integrated Loudness ($I$):** Dual-stage gating (absolute threshold at -70 LUFS, relative threshold at -10 LU).
- **Momentary Loudness ($M$):** 400 ms sliding rectangular window.
- **Short-Term Loudness ($S$):** 3.0 s sliding rectangular window.
- **Loudness Range (LRA):** Statistical short-term distribution with -70 LUFS absolute and -20 LU relative gating, calculating the difference between the 95th and 10th percentiles.

### C. Stereo Phase Correlation & Mono Downmix Analysis
Continuous mono compatibility tracking via Pearson correlation coefficient $\rho_{LR} \in [-1.0, +1.0]$ across 200 ms sliding blocks:
$$\rho_{LR} = \frac{\sum (L - \bar{L})(R - \bar{R})}{\sqrt{\sum (L - \bar{L})^2 \sum (R - \bar{R})^2}}$$
AudioCheck also evaluates **Mono Downmix Attenuation (dB)**, measuring physical energy reduction when stereo channels are summed ($M = \frac{L + R}{2}$). If attenuation exceeds 3.0 dB, phase cancellation is flagged.

### D. Sub-Millisecond Edge Silence Analysis
Top-and-tail inspection using a 5 ms sliding RMS window with 1 ms hop size, isolating exact lead-in and lead-out room tone duration to satisfy strict platform submission boundaries.

### E. Digital Flat-Top Saturation Detection
Distinguishes transient inter-sample peaks from physical converter clipping by tracking consecutive sequences of $N \ge 3$ samples at $\ge 0.999$ full scale.

---

## 4. Benchmark Validation & Ground Truth Accuracy

- **EBU Tech 3341 / 3342 Ground Truth:** 100% pass rate across the official EBU synthetic test set (`ebu-loudness-test-setv05`).
- **Real-World Broadcast Suite (EBU SQAM & Film Stems):** Cross-validated against FFmpeg `libebur128` across 20-minute multi-channel programme audio with zero deviation in integrated loudness or LRA.
- **ICASSP 2024 Degraded LibriSpeech Dataset:** 97.8% accuracy, 100% precision (0 false positives), and 0.980 F1-score across 45 speech files with sub-threshold flat-top clipping.
- **Commercial Validation vs Mastering The Mix EXPOSE:** Bit-perfect sample peak match (1.02 dBFS vs 1.02 dB) and 0.03 LU loudness agreement on commercial music stems.
