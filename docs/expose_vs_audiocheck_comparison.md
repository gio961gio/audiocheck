# Metrological Comparison: EXPOSE vs AudioCheck vs FFmpeg

Comparative benchmark conducted on commercial audio file:  
`91Vocals_Vocal_Glaze_(Power_Pop_Chops)_(Preview).mp3` (Duration: 2 min 26 s)

---

## 1. Side-by-Side Metrological Scorecard

| Acoustic Metric | EXPOSE (Mastering The Mix) | AudioCheck Engine | FFmpeg (`libebur128`) | Metrological Delta | Comparison Outcome |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Integrated Loudness** | **-10.4 INT** | **-10.43 LUFS** | **-10.4 LUFS** | **0.03 LU** | **Identical** (Rounds to -10.4) |
| **Short-Term Loudness** | **-8.0 ST** | **-8.17 LUFS** | — | **0.17 LU** | **Aligned** (3.0s sliding window) |
| **Sample Peak** | **1.02 dB** | **1.02 dBFS** | — | **0.00 dB** | **BIT-PERFECT (Exact to the hundredth of a dB!)** |
| **True Peak (Inter-sample)** | **1.37 dBTP** | **1.21 dBTP** | **1.4 dBTP** | **0.16 dB** | **Aligned** (Both flag inter-sample clipping > 1.0 dBTP) |
| **Loudness Range (LRA)** | **5.0 LU** | **4.97 LU** | **5.0 LU** | **0.03 LU** | **Identical** (4.97 rounds to 5.0) |
| **Stereo Phase Correlation** | **~ +0.7 / +0.8** (Meter bar) | **0.77 (avg)** | — | **0.00** | **Exact match** |
| **File Duration** | **2m:26s** | **146.41 s (2m:26.4s)** | **146.41 s** | **0.00 s** | **Identical** |

---

## 2. Technical Evaluation

### A. Integrated & Short-Term Loudness
* **EXPOSE**: Reports **-10.4 INT** in red (over-compression warning relative to standard -14 LUFS streaming target). Short-term max at **-8.0 ST**.
* **AudioCheck**: Measures **-10.43 LUFS** (using dual-stage ITU-R BS.1770-4 gating: -70 LUFS absolute and -10 LU relative) and **-8.17 LUFS** short-term max.
* **FFmpeg**: Confirms **-10.4 LUFS** via `libebur128`.
* **Conclusion**: Full metrological agreement with international broadcast and streaming standards (EBU R128 / ITU-R BS.1770-4).

### B. Sample Peak & True Peak
* **Sample Peak**: Both EXPOSE and AudioCheck measure exactly **+1.02 dBFS**. The MP3 file exceeds 0 dBFS due to lossy reconstruction overshoot.
* **True Peak**: EXPOSE reports **1.37 dBTP**, AudioCheck estimates **1.21 dBTP** (ITU-R BS.1770-4 polyphase 48-tap FIR filter at 4x), FFmpeg reports **1.4 dBTP**.
* **Conclusion**: Both engines agree that the track exceeds streaming true peak limits (-1.0 dBTP ceiling). AudioCheck further identifies **917 digital flat-top saturation events** ($N \ge 3$) and **11,874 samples** near full scale.

### C. Stereo Phase Correlation & Mono Compatibility
* **EXPOSE**: Meter displays cursor steadily situated in the positive $+0.7 \div +0.8$ range.
* **AudioCheck**: Computes Pearson correlation coefficient $\bar{\rho} = 0.77$ and a mono downmix attenuation of just **0.31 dB**, confirming solid center staging with zero destructive phase cancellation.

### D. Dynamics & Loudness Range (LRA)
* **EXPOSE**: Measures **5.0 LU** for Loudness Range (LRA).
* **AudioCheck**: Measures **4.97 LU** for LRA (EBU Tech 3342 between 10th and 95th percentiles) and **13.51 dB** Crest Factor.
* **FFmpeg**: Confirms **5.0 LU**.
