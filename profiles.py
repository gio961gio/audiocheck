"""Built-in demonstration profiles and JSON import/export helpers."""
from __future__ import annotations

import json
import math
from typing import Any

from audiocheck_core import QCSettings


BUILT_IN_PROFILES: dict[str, dict[str, Any]] = {
    "Podcast & Streaming (AES TD1004 / Spotify / Apple)": {
        "description": "Industry standard for podcasts and streaming platforms (-16 LUFS, true peak max -1.0 dBTP, LRA max 12 LU, stereo phase correlation).",
        "settings": QCSettings(
            target_lufs=-16.0,
            lufs_tolerance=1.5,
            true_peak_ceiling_dbtp=-1.0,
            max_edge_silence_s=2.0,
            dc_offset_limit_dbfs=-60.0,
            silence_threshold_dbfs=-60.0,
            min_silence_region_s=0.25,
            clipping_threshold=0.999,
            oversampling_factor=4,
            max_lra_lu=12.0,
            max_momentary_lufs=-12.0,
            max_short_term_lufs=-14.0,
            min_phase_correlation=0.1,
            max_mono_drop_db=3.5,
            max_flat_top_samples=0,
        ).to_dict(),
    },
    "Broadcast TV & Radio (EBU R128)": {
        "description": "European broadcast standard for TV and radio distribution (-23 LUFS ±0.5 LU, max -1.0 dBTP, max LRA 18 LU).",
        "settings": QCSettings(
            target_lufs=-23.0,
            lufs_tolerance=0.5,
            true_peak_ceiling_dbtp=-1.0,
            max_edge_silence_s=2.0,
            dc_offset_limit_dbfs=-60.0,
            silence_threshold_dbfs=-60.0,
            min_silence_region_s=0.25,
            clipping_threshold=0.999,
            oversampling_factor=4,
            max_lra_lu=18.0,
            max_momentary_lufs=-15.0,
            max_short_term_lufs=-18.0,
            min_phase_correlation=0.2,
            max_mono_drop_db=3.0,
            max_flat_top_samples=0,
        ).to_dict(),
    },
    "Audiobook (ACX / Audible Standard)": {
        "description": "Official ACX submission specifications (-20 LUFS target, peak max -3.0 dBTP, noise floor < -60 dBFS, head/tail silence <= 1.0s).",
        "settings": QCSettings(
            target_lufs=-20.0,
            lufs_tolerance=2.0,
            true_peak_ceiling_dbtp=-3.0,
            max_edge_silence_s=1.0,
            dc_offset_limit_dbfs=-65.0,
            silence_threshold_dbfs=-60.0,
            min_silence_region_s=0.20,
            clipping_threshold=0.999,
            oversampling_factor=4,
            max_lra_lu=10.0,
            max_momentary_lufs=-16.0,
            max_short_term_lufs=-18.0,
            min_phase_correlation=0.3,
            max_mono_drop_db=3.0,
            max_flat_top_samples=0,
        ).to_dict(),
    },
    "Music Streaming (Mastering Target)": {
        "description": "Mastering targets for commercial streaming (-14 LUFS, max -1.0 dBTP, guaranteed mono compatibility).",
        "settings": QCSettings(
            target_lufs=-14.0,
            lufs_tolerance=1.5,
            true_peak_ceiling_dbtp=-1.0,
            max_edge_silence_s=3.0,
            dc_offset_limit_dbfs=-60.0,
            silence_threshold_dbfs=-60.0,
            min_silence_region_s=0.25,
            clipping_threshold=0.999,
            oversampling_factor=4,
            max_lra_lu=16.0,
            max_momentary_lufs=-10.0,
            max_short_term_lufs=-12.0,
            min_phase_correlation=0.0,
            max_mono_drop_db=3.5,
            max_flat_top_samples=0,
        ).to_dict(),
    },
    "General Purpose / Custom QC": {
        "description": "Open reference profile for general QA analysis and custom calibration.",
        "settings": QCSettings().to_dict(),
    },
}


def settings_from_payload(payload: Any) -> tuple[str, QCSettings]:
    """Validate and parse either a wrapped profile JSON or a plain settings object."""
    if not isinstance(payload, dict):
        raise ValueError("JSON payload must be an object.")

    profile_name = str(payload.get("profile_name", "Imported Profile"))[:100]
    raw_settings = payload.get("settings", payload)
    if not isinstance(raw_settings, dict):
        raise ValueError("The 'settings' field must be a JSON object.")

    defaults = QCSettings().to_dict()
    unknown = sorted(set(raw_settings) - set(defaults))
    if unknown:
        raise ValueError("Unrecognized fields in profile: " + ", ".join(unknown))

    converted: dict[str, Any] = {}
    for key, default in defaults.items():
        value = raw_settings.get(key, default)
        if key in ("oversampling_factor", "max_flat_top_samples"):
            if isinstance(value, bool) or not isinstance(value, int):
                raise ValueError(f"'{key}' must be an integer.")
            converted[key] = value
        else:
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(f"'{key}' must be numeric.")
            if not math.isfinite(float(value)):
                raise ValueError(f"'{key}' must be finite.")
            converted[key] = float(value)

    try:
        settings = QCSettings(**converted)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid profile configuration: {exc}") from exc
    return profile_name, settings


def profile_json(profile_name: str, settings: QCSettings) -> bytes:
    """Serialize a portable, human-readable profile file."""
    payload = {
        "profile_name": profile_name,
        "profile_format_version": 2,
        "note": "AudioCheck QC Profile conforming to international audio engineering specifications.",
        "settings": settings.to_dict(),
    }
    return (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
