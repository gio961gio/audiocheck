"""Ground Truth Dataset Generator for AudioCheck.

Generates calibrated audio test sequences compliant with EBU Tech 3341,
EBU Tech 3342, and ITU-R BS.1770-4, together with their analytical
ground truth specifications.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
import numpy as np
import soundfile as sf


DATASET_DIR = Path(__file__).resolve().parent.parent / "datasets" / "ebu_compliance"


def generate_dataset() -> tuple[Path, dict]:
    DATASET_DIR.mkdir(parents=True, exist_ok=True)
    catalog: dict[str, dict] = {}

    sr_standard = 48000

    # -------------------------------------------------------------------------
    # 1. EBU Tech 3341 Sequence 1: 1000 Hz Stereo Sine at -23.0 LUFS
    # -------------------------------------------------------------------------
    duration_s = 10.0
    t = np.arange(int(sr_standard * duration_s)) / sr_standard
    a_23 = 0.07107803213926471
    sine_23 = a_23 * np.sin(2.0 * np.pi * 1000.0 * t)
    sig_23 = np.column_stack([sine_23, sine_23]).astype(np.float32)
    path_23 = DATASET_DIR / "seq_3341_1000hz_23lufs.wav"
    sf.write(path_23, sig_23, sr_standard, subtype="PCM_24")

    catalog[path_23.name] = {
        "description": "EBU Tech 3341 Seq 1: 1kHz in-phase stereo sine wave",
        "sample_rate_hz": sr_standard,
        "channels": 2,
        "duration_s": duration_s,
        "metrics": {
            "integrated_lufs": {"target": -23.00, "tolerance": 0.10, "unit": "LUFS"},
            "momentary_max_lufs": {"target": -23.00, "tolerance": 0.10, "unit": "LUFS"},
            "short_term_max_lufs": {"target": -23.00, "tolerance": 0.10, "unit": "LUFS"},
            "estimated_true_peak_dbtp": {"target": -22.96, "tolerance": 0.10, "unit": "dBTP"},
            "sample_peak_dbfs": {"target": -22.97, "tolerance": 0.05, "unit": "dBFS"},
            "stereo_correlation_avg": {"target": 1.00, "tolerance": 0.01, "unit": ""},
            "mono_drop_db": {"target": 0.00, "tolerance": 0.05, "unit": "dB"},
            "flat_top_samples": {"target": 0, "tolerance": 0, "unit": "samples"},
        },
    }

    # -------------------------------------------------------------------------
    # 2. EBU Tech 3341 Sequence 2: 1000 Hz Stereo Sine at -33.0 LUFS (20s for EBU 3342 LRA = 0.0 LU)
    # -------------------------------------------------------------------------
    duration_s_33 = 20.0
    t_33 = np.arange(int(sr_standard * duration_s_33)) / sr_standard
    a_33 = a_23 * 10.0 ** (-10.0 / 20.0)
    sine_33 = a_33 * np.sin(2.0 * np.pi * 1000.0 * t_33)
    sig_33 = np.column_stack([sine_33, sine_33]).astype(np.float32)
    path_33 = DATASET_DIR / "seq_3341_1000hz_33lufs.wav"
    sf.write(path_33, sig_33, sr_standard, subtype="PCM_24")

    catalog[path_33.name] = {
        "description": "EBU Tech 3341 Seq 2: 1kHz stereo sine wave at -33 LUFS (20s)",
        "sample_rate_hz": sr_standard,
        "channels": 2,
        "duration_s": duration_s_33,
        "metrics": {
            "integrated_lufs": {"target": -33.00, "tolerance": 0.10, "unit": "LUFS"},
            "loudness_range_lu": {"target": 0.00, "tolerance": 0.10, "unit": "LU"},
            "estimated_true_peak_dbtp": {"target": -32.96, "tolerance": 0.10, "unit": "dBTP"},
            "stereo_correlation_avg": {"target": 1.00, "tolerance": 0.01, "unit": ""},
        },
    }

    # -------------------------------------------------------------------------
    # 3. EBU Tech 3341 Table 1: True Peak Intersample Overshoot Pattern (+3.01 dBTP)
    # -------------------------------------------------------------------------
    n_tp = np.arange(int(sr_standard * 5.0))
    s_tp = np.sqrt(2.0) * np.sin(2.0 * np.pi * 0.25 * n_tp + np.pi / 4.0)
    sig_tp = np.column_stack([s_tp, s_tp]).astype(np.float32)
    path_tp = DATASET_DIR / "seq_3341_true_peak_overshoot.wav"
    sf.write(path_tp, sig_tp, sr_standard, subtype="PCM_24")

    catalog[path_tp.name] = {
        "description": "EBU Tech 3341 Inter-sample Peak test signal (fs/4 at pi/4)",
        "sample_rate_hz": sr_standard,
        "channels": 2,
        "duration_s": 5.0,
        "metrics": {
            "sample_peak_dbfs": {"target": 0.00, "tolerance": 0.02, "unit": "dBFS"},
            "estimated_true_peak_dbtp": {"target": 3.01, "tolerance": 0.15, "unit": "dBTP"},
        },
    }

    # -------------------------------------------------------------------------
    # 4. Gated Loudness Step Sequence (-30 LUFS, -75 LUFS quiet, -20 LUFS)
    # -------------------------------------------------------------------------
    t_seg = np.arange(int(sr_standard * 10.0)) / sr_standard
    a_20 = a_23 * 10.0 ** (3.0 / 20.0)
    a_quiet = a_23 * 10.0 ** (-52.0 / 20.0)  # -75 LUFS (below absolute gate -70 LUFS)
    seg_30 = a_33 * np.sin(2.0 * np.pi * 1000.0 * t_seg)
    seg_quiet = a_quiet * np.sin(2.0 * np.pi * 1000.0 * t_seg)
    seg_20 = a_20 * np.sin(2.0 * np.pi * 1000.0 * t_seg)
    sig_gate_mono = np.concatenate([seg_30, seg_quiet, seg_20])
    sig_gate = np.column_stack([sig_gate_mono, sig_gate_mono]).astype(np.float32)
    path_gate = DATASET_DIR / "seq_3341_gated_loudness.wav"
    sf.write(path_gate, sig_gate, sr_standard, subtype="PCM_24")

    catalog[path_gate.name] = {
        "description": "EBU Tech 3341 Gated Loudness test (3 segments: -30, -75, -20 LUFS)",
        "sample_rate_hz": sr_standard,
        "channels": 2,
        "duration_s": 30.0,
        "metrics": {
            "integrated_lufs": {"target": -20.07, "tolerance": 0.10, "unit": "LUFS"},
        },
    }

    # -------------------------------------------------------------------------
    # 5. EBU Tech 3342 Loudness Range (LRA = 10.2 LU)
    # -------------------------------------------------------------------------
    t_lra = np.arange(int(sr_standard * 12.0)) / sr_standard
    a_lra_high = 0.071
    a_lra_low = 0.022
    s_lra_1 = a_lra_high * np.sin(2.0 * np.pi * 1000.0 * t_lra)
    s_lra_2 = a_lra_low * np.sin(2.0 * np.pi * 1000.0 * t_lra)
    sig_lra_m = np.concatenate([s_lra_1, s_lra_2])
    sig_lra = np.column_stack([sig_lra_m, sig_lra_m]).astype(np.float32)
    path_lra = DATASET_DIR / "seq_3342_lra_10lu.wav"
    sf.write(path_lra, sig_lra, sr_standard, subtype="PCM_24")

    catalog[path_lra.name] = {
        "description": "EBU Tech 3342 Controlled Loudness Range (LRA) sequence",
        "sample_rate_hz": sr_standard,
        "channels": 2,
        "duration_s": 24.0,
        "metrics": {
            "integrated_lufs": {"target": -25.62, "tolerance": 0.20, "unit": "LUFS"},
            "loudness_range_lu": {"target": 10.18, "tolerance": 0.20, "unit": "LU"},
        },
    }

    # -------------------------------------------------------------------------
    # 6. Stereo Phase Quadrature (90 deg out-of-phase: corr = 0.00, drop = 3.01 dB)
    # -------------------------------------------------------------------------
    t_phase = np.arange(int(sr_standard * 4.0)) / sr_standard
    l_quad = np.sin(2.0 * np.pi * 440.0 * t_phase) * 0.5
    r_quad = np.cos(2.0 * np.pi * 440.0 * t_phase) * 0.5
    sig_quad = np.column_stack([l_quad, r_quad]).astype(np.float32)
    path_quad = DATASET_DIR / "seq_phase_stereo_quadrature.wav"
    sf.write(path_quad, sig_quad, sr_standard, subtype="PCM_24")

    catalog[path_quad.name] = {
        "description": "Stereo phase quadrature (90 deg shift: corr=0.00, mono drop=3.01 dB)",
        "sample_rate_hz": sr_standard,
        "channels": 2,
        "duration_s": 4.0,
        "metrics": {
            "stereo_correlation_avg": {"target": 0.00, "tolerance": 0.01, "unit": ""},
            "mono_drop_db": {"target": 3.01, "tolerance": 0.05, "unit": "dB"},
        },
    }

    # -------------------------------------------------------------------------
    # 7. Stereo Anti-Phase (180 deg out-of-phase: corr = -1.00, drop = 60.0 dB)
    # -------------------------------------------------------------------------
    l_anti = np.sin(2.0 * np.pi * 440.0 * t_phase) * 0.5
    r_anti = -l_anti
    sig_anti = np.column_stack([l_anti, r_anti]).astype(np.float32)
    path_anti = DATASET_DIR / "seq_phase_stereo_antiphase.wav"
    sf.write(path_anti, sig_anti, sr_standard, subtype="PCM_24")

    catalog[path_anti.name] = {
        "description": "Stereo anti-phase (180 deg inversion: corr=-1.00, total mono cancel)",
        "sample_rate_hz": sr_standard,
        "channels": 2,
        "duration_s": 4.0,
        "metrics": {
            "stereo_correlation_avg": {"target": -1.00, "tolerance": 0.01, "unit": ""},
            "mono_drop_db": {"target": 60.00, "tolerance": 0.50, "unit": "dB"},
        },
    }

    # -------------------------------------------------------------------------
    # 8. Flat-Top Digital Clipping: exactly 50 consecutive clipped samples on channel 0
    # -------------------------------------------------------------------------
    sig_clip = np.zeros((sr_standard * 3, 2), dtype=np.float32)
    t_bg = np.arange(sr_standard * 3) / sr_standard
    bg = 0.05 * np.sin(2.0 * np.pi * 300.0 * t_bg)
    sig_clip[:, 0] = bg
    sig_clip[:, 1] = bg
    sig_clip[10000:10050, 0] = 1.0000  # Exactly 50 clipped samples
    path_clip = DATASET_DIR / "seq_flattop_clipping_50samples.wav"
    sf.write(path_clip, sig_clip, sr_standard, subtype="PCM_24")

    catalog[path_clip.name] = {
        "description": "Flat-top digital clipping with exactly 50 consecutive full-scale samples",
        "sample_rate_hz": sr_standard,
        "channels": 2,
        "duration_s": 3.0,
        "metrics": {
            "flat_top_samples": {"target": 50, "tolerance": 0, "unit": "samples"},
        },
    }

    # -------------------------------------------------------------------------
    # 9. Edge Silence Precision: exactly 0.500s leading and 1.200s trailing
    # -------------------------------------------------------------------------
    lead_s = 0.500
    trail_s = 1.200
    active_s = 2.000
    n_lead = int(lead_s * sr_standard)
    n_active = int(active_s * sr_standard)
    n_trail = int(trail_s * sr_standard)

    tone_act = 0.4 * np.sin(2.0 * np.pi * 440.0 * np.arange(n_active) / sr_standard)
    sig_edge_m = np.zeros(n_lead + n_active + n_trail, dtype=np.float32)
    sig_edge_m[n_lead:n_lead + n_active] = tone_act
    sig_edge = np.column_stack([sig_edge_m, sig_edge_m])
    path_edge = DATASET_DIR / "seq_edge_silence_precise.wav"
    sf.write(path_edge, sig_edge, sr_standard, subtype="PCM_24")

    catalog[path_edge.name] = {
        "description": "Calibrated boundary silence (0.500s leading, 1.200s trailing)",
        "sample_rate_hz": sr_standard,
        "channels": 2,
        "duration_s": lead_s + active_s + trail_s,
        "metrics": {
            "leading_silence_s": {"target": 0.496, "tolerance": 0.008, "unit": "s"},
            "trailing_silence_s": {"target": 1.196, "tolerance": 0.008, "unit": "s"},
        },
    }

    # -------------------------------------------------------------------------
    # 10. Calibrated DC Offset (-40.00 dBFS -> C = 0.0100)
    # -------------------------------------------------------------------------
    c_offset = 0.0100  # -40.00 dBFS
    t_dc = np.arange(int(sr_standard * 3.0)) / sr_standard
    tone_dc = 0.2 * np.sin(2.0 * np.pi * 500.0 * t_dc) + c_offset
    sig_dc = np.column_stack([tone_dc, tone_dc]).astype(np.float32)
    path_dc = DATASET_DIR / "seq_dc_offset_minus40dbfs.wav"
    sf.write(path_dc, sig_dc, sr_standard, subtype="PCM_24")

    catalog[path_dc.name] = {
        "description": "Calibrated DC offset (+0.0100 linear -> -40.00 dBFS)",
        "sample_rate_hz": sr_standard,
        "channels": 2,
        "duration_s": 3.0,
        "metrics": {
            "dc_offset_dbfs": {"target": -40.00, "tolerance": 0.10, "unit": "dBFS"},
        },
    }

    # -------------------------------------------------------------------------
    # 11. Speech Formants Simulation with Natural Cadence & Dynamics
    # -------------------------------------------------------------------------
    t_sp = np.arange(int(sr_standard * 6.0)) / sr_standard
    f0 = 120.0
    glottal = (np.sin(2.0 * np.pi * f0 * t_sp) > 0).astype(np.float32) * 0.1
    formant = (
        0.5 * np.sin(2.0 * np.pi * 500.0 * t_sp)
        + 0.3 * np.sin(2.0 * np.pi * 1500.0 * t_sp)
        + 0.15 * np.sin(2.0 * np.pi * 2500.0 * t_sp)
    )
    syllables = np.abs(np.sin(2.0 * np.pi * 3.5 * t_sp)) ** 1.5
    syllables[(t_sp >= 2.8) & (t_sp <= 3.2)] = 0.0
    speech_signal = (formant * syllables * 0.2).astype(np.float32)
    sig_sp = np.column_stack([speech_signal, speech_signal])
    path_sp = DATASET_DIR / "seq_speech_formants_cadence.wav"
    sf.write(path_sp, sig_sp, sr_standard, subtype="PCM_24")

    catalog[path_sp.name] = {
        "description": "Speech acoustic simulation with dynamic vocal formants and 400ms pause",
        "sample_rate_hz": sr_standard,
        "channels": 2,
        "duration_s": 6.0,
        "metrics": {
            "integrated_lufs": {"target": -22.13, "tolerance": 0.15, "unit": "LUFS"},
            "crest_factor_db": {"target": 7.37, "tolerance": 0.15, "unit": "dB"},
        },
    }

    # -------------------------------------------------------------------------
    # 12. High-Resolution 96 kHz Audio File
    # -------------------------------------------------------------------------
    sr_96k = 96000
    t_96k = np.arange(int(sr_96k * 3.0)) / sr_96k
    sig_96k_m = a_23 * np.sin(2.0 * np.pi * 1000.0 * t_96k)
    sig_96k = np.column_stack([sig_96k_m, sig_96k_m]).astype(np.float32)
    path_96k = DATASET_DIR / "seq_multirate_96k_highres.wav"
    sf.write(path_96k, sig_96k, sr_96k, subtype="PCM_24")

    catalog[path_96k.name] = {
        "description": "High-resolution 96 kHz 24-bit test sequence",
        "sample_rate_hz": sr_96k,
        "channels": 2,
        "duration_s": 3.0,
        "metrics": {
            "sample_rate_hz": {"target": 96000, "tolerance": 0, "unit": "Hz"},
            "integrated_lufs": {"target": -23.00, "tolerance": 0.15, "unit": "LUFS"},
        },
    }

    # -------------------------------------------------------------------------
    # 13. Sub-Frame Short Burst (250 ms < 400 ms momentary window)
    # -------------------------------------------------------------------------
    t_short = np.arange(int(sr_standard * 0.250)) / sr_standard
    sig_short_m = 0.2 * np.sin(2.0 * np.pi * 800.0 * t_short)
    sig_short = np.column_stack([sig_short_m, sig_short_m]).astype(np.float32)
    path_short = DATASET_DIR / "seq_subframe_short_burst_250ms.wav"
    sf.write(path_short, sig_short, sr_standard, subtype="PCM_24")

    catalog[path_short.name] = {
        "description": "Sub-frame 250ms short burst (< 400ms momentary window)",
        "sample_rate_hz": sr_standard,
        "channels": 2,
        "duration_s": 0.250,
        "metrics": {
            "duration_s": {"target": 0.250, "tolerance": 0.005, "unit": "s"},
        },
    }

    # Save ground truth catalog to JSON
    json_path = DATASET_DIR / "ground_truth.json"
    json_path.write_text(json.dumps(catalog, indent=2, ensure_ascii=False), encoding="utf-8")
    return json_path, catalog


if __name__ == "__main__":
    out_json, cat = generate_dataset()
    print(f"[OK] Dataset generato con successo: {len(cat)} file audio con Ground Truth in {out_json}")
