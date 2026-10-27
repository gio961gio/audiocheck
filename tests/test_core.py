import io
import numpy as np
import pytest
import soundfile as sf

from audiocheck_core import (
    QCSettings,
    analyze_audio,
    calculate_loudness_suite,
    calculate_stereo_correlation,
    detect_flat_top_clipping,
    detect_silence_regions,
    estimate_true_peak,
    measure_edge_silence,
)
from engine.runner import BatchRunner


def wav_bytes(audio: np.ndarray, sample_rate: int = 48000) -> bytes:
    buffer = io.BytesIO()
    sf.write(buffer, audio, sample_rate, format="WAV", subtype="FLOAT")
    return buffer.getvalue()


def test_detects_leading_and_trailing_silence_regions():
    sr = 48000
    silence = np.zeros((int(0.6 * sr), 1), dtype=np.float32)
    tone = (0.1 * np.sin(2 * np.pi * 440 * np.arange(sr) / sr)).astype(np.float32).reshape(-1, 1)
    audio = np.vstack([silence, tone, silence])
    regions = detect_silence_regions(audio, sr, threshold_dbfs=-60, min_duration_s=0.25)
    assert len(regions) == 2
    assert abs(regions[0]["duration_s"] - 0.6) <= 0.02
    assert abs(regions[1]["duration_s"] - 0.6) <= 0.02


def test_measure_edge_silence_millisecond_precision():
    sr = 48000
    sil_lead = np.zeros((int(0.35 * sr), 1), dtype=np.float32)
    tone = (0.2 * np.sin(2 * np.pi * 440 * np.arange(sr) / sr)).astype(np.float32).reshape(-1, 1)
    sil_trail = np.zeros((int(0.72 * sr), 1), dtype=np.float32)
    audio = np.vstack([sil_lead, tone, sil_trail])

    lead_s, trail_s = measure_edge_silence(audio, sr, threshold_dbfs=-60.0)
    assert abs(lead_s - 0.35) <= 0.015
    assert abs(trail_s - 0.72) <= 0.015


def test_measure_edge_silence_pure_silence():
    sr = 48000
    audio = np.zeros((int(1.5 * sr), 2), dtype=np.float32)
    lead_s, trail_s = measure_edge_silence(audio, sr, threshold_dbfs=-60.0)
    assert abs(lead_s - 1.5) <= 0.001
    assert abs(trail_s - 1.5) <= 0.001


def test_analyzer_reports_core_metadata_and_checks():
    sr = 48000
    t = np.arange(sr) / sr
    audio = (0.2 * np.sin(2 * np.pi * 440 * t)).astype(np.float32).reshape(-1, 1)
    result = analyze_audio(wav_bytes(audio, sr), "tone.wav", QCSettings())
    assert result["filename"] == "tone.wav"
    assert result["sample_rate_hz"] == sr
    assert result["channels"] == 1
    assert abs(result["duration_s"] - 1.0) < 0.001
    assert result["sample_peak_dbfs"] < 0
    assert {"Integrated Loudness", "Estimated True Peak", "DC Offset", "Dynamic Range (Crest Factor)"}.issubset({c["check"] for c in result["checks"]})


def test_short_signal_under_400ms_handles_loudness_gracefully():
    sr = 48000
    t = np.arange(int(0.2 * sr)) / sr  # 200ms
    audio = (0.5 * np.sin(2 * np.pi * 1000 * t)).astype(np.float32).reshape(-1, 1)
    result = analyze_audio(wav_bytes(audio, sr), "short.wav", QCSettings())
    assert result["integrated_lufs"] is None
    lufs_check = next(c for c in result["checks"] if c["check"] == "Integrated Loudness")
    assert lufs_check["status"] == "WARN"
    assert lufs_check["value"] == "N/D"


def test_stereo_channel_analysis():
    sr = 48000
    t = np.arange(sr) / sr
    left = 0.2 * np.sin(2 * np.pi * 440 * t)
    right = 0.4 * np.sin(2 * np.pi * 880 * t)
    audio = np.column_stack([left, right]).astype(np.float32)
    result = analyze_audio(wav_bytes(audio, sr), "stereo.wav", QCSettings())
    assert result["channels"] == 2
    assert result["sample_peak_dbfs"] > -10.0
    assert "Stereo Phase Correlation" in {c["check"] for c in result["checks"]}


def test_stereo_phase_correlation_and_mono_drop():
    sr = 48000
    t = np.arange(sr) / sr
    sig = 0.3 * np.sin(2 * np.pi * 440 * t)

    # 1. Perfectly in-phase
    in_phase = np.column_stack([sig, sig])
    avg_corr, min_corr, drop_db = calculate_stereo_correlation(in_phase, sr)
    assert avg_corr == 1.0
    assert drop_db == 0.0

    # 2. Completely out-of-phase (180 deg)
    out_phase = np.column_stack([sig, -sig])
    avg_corr_out, min_corr_out, drop_db_out = calculate_stereo_correlation(out_phase, sr)
    assert avg_corr_out == -1.0
    assert drop_db_out >= 50.0  # Massive cancellation

    # 3. Decorrelated
    np.random.seed(42)
    uncorr = np.column_stack([np.random.randn(sr) * 0.1, np.random.randn(sr) * 0.1])
    avg_u, min_u, drop_u = calculate_stereo_correlation(uncorr, sr)
    assert abs(avg_u) < 0.1
    assert abs(drop_u - 3.0) < 0.5  # Typical 3 dB drop


def test_flat_top_clipping_detection():
    sr = 48000
    sig = np.zeros((200, 1), dtype=np.float32)
    sig[20:26] = 1.0  # 6 consecutive samples -> 1 event
    sig[100] = 1.0    # 1 isolated sample -> NOT flat-top

    events, samples = detect_flat_top_clipping(sig, threshold=0.999, min_consecutive=3)
    assert events == 1
    assert samples == 6


def test_pure_dc_offset_detection():
    sr = 48000
    audio = np.full((sr, 1), 0.05, dtype=np.float32)
    result = analyze_audio(wav_bytes(audio, sr), "dc.wav", QCSettings(dc_offset_limit_dbfs=-60.0))
    assert result["dc_offset_dbfs"] > -30.0
    dc_check = next(c for c in result["checks"] if c["check"] == "DC Offset")
    assert dc_check["status"] == "WARN"


def test_clipping_is_reported():
    sr = 48000
    audio = np.zeros((sr, 1), dtype=np.float32)
    audio[100:200] = 1.0
    result = analyze_audio(wav_bytes(audio, sr), "clipped.wav", QCSettings())
    assert result["clip_samples"] > 0
    assert result["flat_top_events"] > 0
    clip_check = next(c for c in result["checks"] if c["check"] == "Digital Flat-Top Clipping (N≥3)")
    assert clip_check["status"] == "FAIL"


def test_qc_settings_reject_invalid_thresholds():
    with pytest.raises(ValueError, match="target_lufs"):
        QCSettings(target_lufs=-200)
    with pytest.raises(ValueError, match="max_lra_lu"):
        QCSettings(max_lra_lu=100.0)


def test_ebu_tech_3341_inter_sample_peak_overshoot():
    sr = 48000
    base = np.array([np.sin(np.pi / 4), np.sin(3 * np.pi / 4), np.sin(5 * np.pi / 4), np.sin(7 * np.pi / 4)], dtype=np.float32)
    audio = np.tile(base, 1000).reshape(-1, 1)  # ~83 ms repeated
    result = analyze_audio(wav_bytes(audio, sr), "ebu_synthetic.wav", QCSettings(oversampling_factor=4))
    assert abs(result["sample_peak_dbfs"] - (-3.01)) < 0.1
    overshoot = result["estimated_true_peak_dbtp"] - result["sample_peak_dbfs"]
    assert overshoot > 2.5


def test_loudness_suite_and_lra():
    sr = 48000
    t = np.arange(4 * sr) / sr  # 4 seconds
    audio = (0.3 * np.sin(2 * np.pi * 440 * t) * (1.0 + 0.8 * np.sin(2 * np.pi * 0.5 * t))).astype(np.float32).reshape(-1, 1)

    suite = calculate_loudness_suite(audio, sr)
    assert suite["integrated_lufs"] is not None
    assert suite["momentary_max_lufs"] is not None
    assert suite["loudness_range_lu"] is not None
    assert suite["loudness_range_lu"] > 0.0


def test_crest_factor_and_dynamic_range():
    sr = 48000
    t = np.arange(sr) / sr
    audio = (0.5 * np.sin(2 * np.pi * 440 * t)).astype(np.float32).reshape(-1, 1)
    result = analyze_audio(wav_bytes(audio, sr), "sine.wav", QCSettings())
    # A pure sine wave has crest factor = 3.01 dB (peak/RMS = sqrt(2))
    assert abs(result["crest_factor_db"] - 3.01) <= 0.15


def test_batch_runner_execution():
    sr = 48000
    t = np.arange(sr) / sr
    audio1 = (0.2 * np.sin(2 * np.pi * 440 * t)).astype(np.float32).reshape(-1, 1)
    audio2 = (0.1 * np.sin(2 * np.pi * 880 * t)).astype(np.float32).reshape(-1, 1)

    items = [("file1.wav", wav_bytes(audio1, sr)), ("file2.wav", wav_bytes(audio2, sr))]
    runner = BatchRunner(prefer_threads=True)
    results, failures = runner.run(items, QCSettings())

    assert len(results) == 2
    assert len(failures) == 0
    assert results[0]["filename"] == "file1.wav"
    assert results[1]["filename"] == "file2.wav"
