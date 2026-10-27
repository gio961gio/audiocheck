# AudioCheck — Rapporto Scientifico di Accuratezza e Benchmark DSP

> **Protocollo Metrologico:** Validazione deterministica rispetto alle specifiche analitiche e ai segnali di prova delle raccomandazioni internazionali **ITU-R BS.1770-4**, **EBU Tech 3341** ed **EBU Tech 3342**.

## 1. Indicatori Chiave di Prestazione (KPI)

- **Versione AudioCheck:** `2.0.0`
- **Data Benchmark:** 2026-10-27 06:55:16 UTC
- **Accuratezza Globale del Modello:** **100.0%** (30/30 controlli conformi)
- **Throughput Computazionale:** **39.0× Real-Time**
- **Durata Audio Elaborata:** 115.95 secondi (1.93 minuti)
- **Tempo di Elaborazione su CPU:** 2.975 secondi

## 2. Matrice di Validazione Ground Truth vs AudioCheck

| Esito | File di Test | SHA-256 (Primi 8 car.) | Metrica DSP | Target Ground Truth | Valore Rilevato | Errore Delta ($\Delta$) | Tolleranza Ammessa | Categoria GT |
| :---: | :--- | :---: | :--- | :---: | :---: | :---: | :---: | :--- |
| ✅ PASS | `seq_3341_1000hz_23lufs.wav` | `db57a81e` | **integrated_lufs** | -23.0 LUFS | -23.00 LUFS | 0.0000 | ±0.1 LUFS | `normative_expected` |
| ✅ PASS | `seq_3341_1000hz_23lufs.wav` | `db57a81e` | **momentary_max_lufs** | -23.0 LUFS | -23.00 LUFS | 0.0000 | ±0.1 LUFS | `normative_expected` |
| ✅ PASS | `seq_3341_1000hz_23lufs.wav` | `db57a81e` | **short_term_max_lufs** | -23.0 LUFS | -23.00 LUFS | 0.0000 | ±0.1 LUFS | `normative_expected` |
| ✅ PASS | `seq_3341_1000hz_23lufs.wav` | `db57a81e` | **estimated_true_peak_dbtp** | -22.96 dBTP | -22.96 dBTP | 0.0000 | ±0.1 dBTP | `normative_expected` |
| ✅ PASS | `seq_3341_1000hz_23lufs.wav` | `db57a81e` | **sample_peak_dbfs** | -22.97 dBFS | -22.97 dBFS | 0.0000 | ±0.05 dBFS | `normative_expected` |
| ✅ PASS | `seq_3341_1000hz_23lufs.wav` | `db57a81e` | **stereo_correlation_avg** | 1.0  | 1.00  | 0.0000 | ±0.01  | `normative_expected` |
| ✅ PASS | `seq_3341_1000hz_23lufs.wav` | `db57a81e` | **mono_drop_db** | 0.0 dB | 0.00 dB | 0.0000 | ±0.05 dB | `normative_expected` |
| ✅ PASS | `seq_3341_1000hz_23lufs.wav` | `db57a81e` | **flat_top_samples** | 0 samples | 0.00 samples | 0.0000 | ±0 samples | `normative_expected` |
| ✅ PASS | `seq_3341_1000hz_33lufs.wav` | `af7fb941` | **integrated_lufs** | -33.0 LUFS | -33.00 LUFS | 0.0000 | ±0.1 LUFS | `normative_expected` |
| ✅ PASS | `seq_3341_1000hz_33lufs.wav` | `af7fb941` | **loudness_range_lu** | 0.0 LU | 0.00 LU | 0.0000 | ±0.1 LU | `normative_expected` |
| ✅ PASS | `seq_3341_1000hz_33lufs.wav` | `af7fb941` | **estimated_true_peak_dbtp** | -32.96 dBTP | -32.96 dBTP | 0.0000 | ±0.1 dBTP | `normative_expected` |
| ✅ PASS | `seq_3341_1000hz_33lufs.wav` | `af7fb941` | **stereo_correlation_avg** | 1.0  | 1.00  | 0.0000 | ±0.01  | `normative_expected` |
| ✅ PASS | `seq_3341_true_peak_overshoot.wav` | `03cfb46c` | **sample_peak_dbfs** | 0.0 dBFS | 0.00 dBFS | 0.0000 | ±0.02 dBFS | `normative_expected` |
| ✅ PASS | `seq_3341_true_peak_overshoot.wav` | `03cfb46c` | **estimated_true_peak_dbtp** | 3.01 dBTP | 3.09 dBTP | 0.0800 | ±0.15 dBTP | `normative_expected` |
| ✅ PASS | `seq_3341_gated_loudness.wav` | `b7e43053` | **integrated_lufs** | -20.07 LUFS | -20.07 LUFS | 0.0000 | ±0.1 LUFS | `normative_expected` |
| ✅ PASS | `seq_3342_lra_10lu.wav` | `dd9306d4` | **integrated_lufs** | -25.62 LUFS | -25.62 LUFS | 0.0000 | ±0.2 LUFS | `normative_expected` |
| ✅ PASS | `seq_3342_lra_10lu.wav` | `dd9306d4` | **loudness_range_lu** | 10.18 LU | 10.18 LU | 0.0000 | ±0.2 LU | `normative_expected` |
| ✅ PASS | `seq_phase_stereo_quadrature.wav` | `5a852217` | **stereo_correlation_avg** | 0.0  | 0.00  | 0.0000 | ±0.01  | `normative_expected` |
| ✅ PASS | `seq_phase_stereo_quadrature.wav` | `5a852217` | **mono_drop_db** | 3.01 dB | 3.01 dB | 0.0000 | ±0.05 dB | `normative_expected` |
| ✅ PASS | `seq_phase_stereo_antiphase.wav` | `ec5cebcc` | **stereo_correlation_avg** | -1.0  | -1.00  | 0.0000 | ±0.01  | `normative_expected` |
| ✅ PASS | `seq_phase_stereo_antiphase.wav` | `ec5cebcc` | **mono_drop_db** | 60.0 dB | 60.00 dB | 0.0000 | ±0.5 dB | `normative_expected` |
| ✅ PASS | `seq_flattop_clipping_50samples.wav` | `c60eb98f` | **flat_top_samples** | 50 samples | 50.00 samples | 0.0000 | ±0 samples | `normative_expected` |
| ✅ PASS | `seq_edge_silence_precise.wav` | `f9b9da8a` | **leading_silence_s** | 0.496 s | 0.50 s | 0.0000 | ±0.008 s | `normative_expected` |
| ✅ PASS | `seq_edge_silence_precise.wav` | `f9b9da8a` | **trailing_silence_s** | 1.196 s | 1.20 s | 0.0000 | ±0.008 s | `normative_expected` |
| ✅ PASS | `seq_dc_offset_minus40dbfs.wav` | `198e11dc` | **dc_offset_dbfs** | -40.0 dBFS | -40.00 dBFS | 0.0000 | ±0.1 dBFS | `normative_expected` |
| ✅ PASS | `seq_speech_formants_cadence.wav` | `c03cba6c` | **integrated_lufs** | -22.13 LUFS | -22.13 LUFS | 0.0000 | ±0.15 LUFS | `normative_expected` |
| ✅ PASS | `seq_speech_formants_cadence.wav` | `c03cba6c` | **crest_factor_db** | 7.37 dB | 7.37 dB | 0.0000 | ±0.15 dB | `normative_expected` |
| ✅ PASS | `seq_multirate_96k_highres.wav` | `119c0e67` | **sample_rate_hz** | 96000 Hz | 96000.00 Hz | 0.0000 | ±0 Hz | `normative_expected` |
| ✅ PASS | `seq_multirate_96k_highres.wav` | `119c0e67` | **integrated_lufs** | -23.0 LUFS | -23.00 LUFS | 0.0000 | ±0.15 LUFS | `normative_expected` |
| ✅ PASS | `seq_subframe_short_burst_250ms.wav` | `9b905c5d` | **duration_s** | 0.25 s | 0.25 s | 0.0000 | ±0.005 s | `normative_expected` |