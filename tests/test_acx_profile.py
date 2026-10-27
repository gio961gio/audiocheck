"""Dedicated ACX / Audible Delivery Requirements Boundary Tests.

Verifies AudioCheck behavior exactly on the threshold boundaries defined by
the official ACX Audio Submission Requirements:
- Target loudness / RMS: -20.0 LUFS (range -22.0 to -18.0 LUFS)
- Maximum peak: <= -3.0 dBTP / dBFS
- Noise floor: <= -60.0 dBFS
- Edge silence / room tone: leading/trailing boundaries <= 1.0s
Checked against official ACX specifications on: 2026-10-26
"""
from io import BytesIO
import numpy as np
import pytest
import soundfile as sf

from audiocheck_core import QCSettings, analyze_audio
from profiles import BUILT_IN_PROFILES


@pytest.fixture
def acx_settings() -> QCSettings:
    settings_dict = BUILT_IN_PROFILES["Audiobook (ACX / Audible Standard)"]["settings"]
    return QCSettings(**settings_dict)


def _make_audio_bytes(signal: np.ndarray, sr: int = 44100) -> bytes:
    buf = BytesIO()
    sf.write(buf, signal, sr, format="WAV", subtype="PCM_16")
    return buf.getvalue()


def test_acx_loudness_range_boundaries(acx_settings):
    """Test boundary conditions for ACX loudness: -20.0 LUFS with ±2.0 LU tolerance."""
    sr = 44100
    t = np.arange(int(sr * 4.0)) / sr

    # 1. Nominal center (-20.0 LUFS) -> PASS
    a_center = 0.071078 * 10.0 ** (3.0 / 20.0)
    sig_center = np.column_stack([a_center * np.sin(2 * np.pi * 1000 * t)] * 2)
    res_center = analyze_audio(_make_audio_bytes(sig_center, sr), "acx_center.wav", acx_settings)
    check_center = next(c for c in res_center["checks"] if "Integrated Loudness" in c["check"])
    assert check_center["status"] == "PASS"

    # 2. Lower boundary passing (-21.5 LUFS) -> PASS
    a_low_pass = a_center * 10.0 ** (-1.5 / 20.0)
    sig_low_pass = np.column_stack([a_low_pass * np.sin(2 * np.pi * 1000 * t)] * 2)
    res_low_pass = analyze_audio(_make_audio_bytes(sig_low_pass, sr), "acx_low_pass.wav", acx_settings)
    check_low_pass = next(c for c in res_low_pass["checks"] if "Integrated Loudness" in c["check"])
    assert check_low_pass["status"] == "PASS"

    # 3. Lower boundary failing (-23.0 LUFS, outside ±2.0 of -20.0) -> FAIL
    a_low_fail = a_center * 10.0 ** (-3.0 / 20.0)
    sig_low_fail = np.column_stack([a_low_fail * np.sin(2 * np.pi * 1000 * t)] * 2)
    res_low_fail = analyze_audio(_make_audio_bytes(sig_low_fail, sr), "acx_low_fail.wav", acx_settings)
    check_low_fail = next(c for c in res_low_fail["checks"] if "Integrated Loudness" in c["check"])
    assert check_low_fail["status"] == "FAIL"

    # 4. Upper boundary failing (-17.0 LUFS, too loud for ACX) -> FAIL
    a_high_fail = a_center * 10.0 ** (3.0 / 20.0)
    sig_high_fail = np.column_stack([a_high_fail * np.sin(2 * np.pi * 1000 * t)] * 2)
    res_high_fail = analyze_audio(_make_audio_bytes(sig_high_fail, sr), "acx_high_fail.wav", acx_settings)
    check_high_fail = next(c for c in res_high_fail["checks"] if "Integrated Loudness" in c["check"])
    assert check_high_fail["status"] == "FAIL"


def test_acx_true_peak_ceiling_boundary(acx_settings):
    """ACX strictly requires peak levels <= -3.0 dBTP."""
    sr = 44100
    t = np.arange(int(sr * 2.0)) / sr

    # Below ceiling (-3.5 dBFS) -> PASS
    a_pass = 10.0 ** (-3.5 / 20.0)
    sig_pass = np.column_stack([a_pass * np.sin(2 * np.pi * 500 * t)] * 2)
    res_pass = analyze_audio(_make_audio_bytes(sig_pass, sr), "peak_pass.wav", acx_settings)
    tp_check_pass = next(c for c in res_pass["checks"] if "Estimated True Peak" in c["check"])
    assert tp_check_pass["status"] == "PASS"

    # Exceeding ceiling (-2.0 dBFS) -> FAIL
    a_fail = 10.0 ** (-2.0 / 20.0)
    sig_fail = np.column_stack([a_fail * np.sin(2 * np.pi * 500 * t)] * 2)
    res_fail = analyze_audio(_make_audio_bytes(sig_fail, sr), "peak_fail.wav", acx_settings)
    tp_check_fail = next(c for c in res_fail["checks"] if "Estimated True Peak" in c["check"])
    assert tp_check_fail["status"] == "FAIL"


def test_acx_edge_silence_boundary(acx_settings):
    """ACX recommends between 0.5s and 1.0s leading silence."""
    sr = 44100
    # 0.5s leading silence -> within max_edge_silence_s (1.0s) -> PASS
    lead_ok = int(0.5 * sr)
    act = int(2.0 * sr)
    trail_ok = int(0.5 * sr)
    tone = 0.1 * np.sin(2 * np.pi * 440 * np.arange(act) / sr)
    sig_ok = np.zeros(lead_ok + act + trail_ok, dtype=np.float32)
    sig_ok[lead_ok:lead_ok + act] = tone
    res_ok = analyze_audio(_make_audio_bytes(np.column_stack([sig_ok, sig_ok]), sr), "sil_pass.wav", acx_settings)
    sil_check_ok = next(c for c in res_ok["checks"] if "Edge Silence" in c["check"])
    assert sil_check_ok["status"] == "PASS"

    # 1.8s leading silence -> exceeds max_edge_silence_s (1.0s) -> FAIL
    lead_long = int(1.8 * sr)
    sig_long = np.zeros(lead_long + act + trail_ok, dtype=np.float32)
    sig_long[lead_long:lead_long + act] = tone
    res_long = analyze_audio(_make_audio_bytes(np.column_stack([sig_long, sig_long]), sr), "sil_fail.wav", acx_settings)
    sil_check_fail = next(c for c in res_long["checks"] if "Edge Silence" in c["check"])
    assert sil_check_fail["status"] == "FAIL"


def test_acx_dc_offset_boundary(acx_settings):
    """Test DC offset boundary at -65.0 dBFS."""
    sr = 44100
    t = np.arange(int(sr * 2.0)) / sr
    # Low DC offset: 0.0001 linear -> -80 dBFS -> PASS
    sig_clean = np.column_stack([0.1 * np.sin(2 * np.pi * 440 * t) + 0.0001] * 2)
    res_clean = analyze_audio(_make_audio_bytes(sig_clean, sr), "dc_pass.wav", acx_settings)
    dc_check_pass = next(c for c in res_clean["checks"] if "DC Offset" in c["check"])
    assert dc_check_pass["status"] == "PASS"

    # High DC offset: 0.002 linear -> -54 dBFS -> WARN (exceeds -65 dBFS limit)
    sig_dirty = np.column_stack([0.1 * np.sin(2 * np.pi * 440 * t) + 0.002] * 2)
    res_dirty = analyze_audio(_make_audio_bytes(sig_dirty, sr), "dc_fail.wav", acx_settings)
    dc_check_fail = next(c for c in res_dirty["checks"] if "DC Offset" in c["check"])
    assert dc_check_fail["status"] == "WARN"
    assert res_dirty["dc_offset_dbfs"] > -65.0
