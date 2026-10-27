import html
import json

import pytest

from audiocheck_core import QCSettings
from profiles import BUILT_IN_PROFILES, profile_json, settings_from_payload
from reporting import build_html_report


def test_builtin_profiles_can_be_loaded_and_exported():
    for name, profile in BUILT_IN_PROFILES.items():
        imported_name, settings = settings_from_payload({"profile_name": name, "settings": profile["settings"]})
        assert imported_name == name
        assert settings.to_dict() == profile["settings"]
        saved = json.loads(profile_json(imported_name, settings).decode("utf-8"))
        assert saved["settings"] == settings.to_dict()


def test_profile_import_rejects_out_of_range_values():
    with pytest.raises(ValueError, match="target_lufs"):
        settings_from_payload({"profile_name": "bad", "settings": {"target_lufs": -100}})


def test_html_report_escapes_user_supplied_filename():
    malicious_name = '<audio onmouseover="alert(1)">.wav'
    result = {
        "filename": malicious_name,
        "status": "PASS",
        "duration_s": 1.0,
        "sample_rate_hz": 48000,
        "channels": 1,
        "integrated_lufs": -16.0,
        "sample_peak_dbfs": -2.0,
        "estimated_true_peak_dbtp": -1.8,
        "dc_offset_dbfs": -100.0,
        "leading_silence_s": 0.0,
        "trailing_silence_s": 0.0,
        "total_detected_silence_s": 0.0,
        "checks": [{"check": "Loudness", "status": "PASS", "value": "-16 LUFS", "detail": "OK"}],
    }
    report = build_html_report([result], [], QCSettings().to_dict(), "QC test", generated_at="2026-01-01 00:00 UTC")
    assert html.escape(malicious_name, quote=True) in report
    assert malicious_name not in report
    assert "AudioCheck" in report


def test_html_report_includes_decode_failures():
    report = build_html_report(
        [], [{"filename": "broken.wav", "error": "invalid stream"}],
        QCSettings().to_dict(), "QC test", generated_at="2026-01-01 00:00 UTC",
    )
    assert "broken.wav" in report
    assert "invalid stream" in report
    assert "FAIL" in report


def test_html_report_renders_meter_bars_and_daw_remediation():
    result = {
        "filename": "problematic_master.wav",
        "status": "FAIL",
        "duration_s": 120.0,
        "sample_rate_hz": 48000,
        "channels": 2,
        "integrated_lufs": -9.5,
        "loudness_range_lu": 14.2,
        "estimated_true_peak_dbtp": 1.25,
        "sample_peak_dbfs": 0.0,
        "crest_factor_db": 8.0,
        "stereo_correlation_avg": -0.45,
        "mono_drop_db": 6.2,
        "flat_top_samples": 42,
        "leading_silence_s": 0.0,
        "trailing_silence_s": 0.0,
        "total_detected_silence_s": 0.0,
        "checks": [
            {"check": "Loudness integrato", "status": "FAIL", "value": "-9.5 LUFS", "detail": "Target -16.0 LUFS"},
            {"check": "True peak", "status": "FAIL", "value": "+1.25 dBTP", "detail": "Limite -1.0 dBTP"},
            {"check": "Correlazione fase stereo", "status": "FAIL", "value": "-0.45", "detail": "Rischio cancellazione"},
        ],
    }
    report = build_html_report([result], [], QCSettings().to_dict(), "Podcast & Streaming (AES TD1004 / Spotify / Apple)")
    assert "meter-box" in report
    assert "meter-bar-fill" in report
    assert "DAW Remediation Guide" in report
    assert "Reaper / Pro Tools / Logic / Audition" in report
    assert "True Peak Limiting" in report
