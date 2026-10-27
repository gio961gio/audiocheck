"""Core audio analysis for AudioCheck.

The module intentionally contains no UI code so its DSP functions can be tested
independently and reused by a CLI or future desktop application.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from io import BytesIO
import math
import shutil
import subprocess
from typing import Any

import numpy as np
import soundfile as sf
from scipy.signal import upfirdn, resample_poly

try:
    import pyloudnorm as pyln
except ImportError:  # provide a useful error when the application starts
    pyln = None


# ITU-R BS.1770-4 Annex 2: Reference 48-tap, 4-phase polyphase interpolation filter for 4x oversampling
_ITU_BS1770_PHASES = (
    (0.0017089843750, 0.0109863281250, -0.0196533203125, 0.0332031250000, -0.0594482421875, 0.1373291015625,
     0.9721679687500, -0.1022949218750, 0.0476074218750, -0.0266113281250, 0.0148925781250, -0.0083007812500),
    (-0.0291748046875, 0.0292968750000, -0.0517578125000, 0.0891113281250, -0.1665039062500, 0.4650878906250,
     0.7797851562500, -0.2003173828125, 0.1015625000000, -0.0582275390625, 0.0330810546875, -0.0189208984375),
    (-0.0189208984375, 0.0330810546875, -0.0582275390625, 0.1015625000000, -0.2003173828125, 0.7797851562500,
     0.4650878906250, -0.1665039062500, 0.0891113281250, -0.0517578125000, 0.0292968750000, -0.0291748046875),
    (-0.0083007812500, 0.0148925781250, -0.0266113281250, 0.0476074218750, -0.1022949218750, 0.9721679687500,
     0.1373291015625, -0.0594482421875, 0.0332031250000, -0.0196533203125, 0.0109863281250, 0.0017089843750),
)
_BS1770_48TAP_FIR = np.zeros(48, dtype=np.float64)
for _p in range(4):
    for _k in range(12):
        _BS1770_48TAP_FIR[_k * 4 + _p] = _ITU_BS1770_PHASES[_p][_k]


@dataclass
class QCSettings:
    """Quality-control limits. Defaults align with modern streaming/podcast delivery standards."""
    target_lufs: float = -16.0
    lufs_tolerance: float = 2.0
    true_peak_ceiling_dbtp: float = -1.0
    max_edge_silence_s: float = 2.0
    dc_offset_limit_dbfs: float = -60.0
    silence_threshold_dbfs: float = -60.0
    min_silence_region_s: float = 0.25
    clipping_threshold: float = 0.999
    oversampling_factor: int = 4
    # Phase 2 additions
    max_lra_lu: float = 14.0
    max_momentary_lufs: float = -13.0
    max_short_term_lufs: float = -14.0
    min_phase_correlation: float = 0.0
    max_mono_drop_db: float = 3.5
    max_flat_top_samples: int = 0

    def __post_init__(self) -> None:
        numeric_ranges = {
            "target_lufs": (-36.0, 0.0),
            "lufs_tolerance": (0.0, 12.0),
            "true_peak_ceiling_dbtp": (-12.0, 3.0),
            "max_edge_silence_s": (0.0, 30.0),
            "dc_offset_limit_dbfs": (-120.0, 0.0),
            "silence_threshold_dbfs": (-100.0, -10.0),
            "min_silence_region_s": (0.01, 30.0),
            "clipping_threshold": (0.5, 1.0),
            "max_lra_lu": (1.0, 50.0),
            "max_momentary_lufs": (-36.0, 0.0),
            "max_short_term_lufs": (-36.0, 0.0),
            "min_phase_correlation": (-1.0, 1.0),
            "max_mono_drop_db": (0.0, 60.0),
        }
        for field_name, (minimum, maximum) in numeric_ranges.items():
            value = getattr(self, field_name)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(f"{field_name} deve essere numerico.")
            if not math.isfinite(float(value)) or not minimum <= float(value) <= maximum:
                raise ValueError(f"{field_name} deve essere compreso tra {minimum} e {maximum}.")

        for int_field, (min_int, max_int) in [
            ("oversampling_factor", (1, 16)),
            ("max_flat_top_samples", (0, 1000000)),
        ]:
            val = getattr(self, int_field)
            if isinstance(val, bool) or not isinstance(val, int):
                raise ValueError(f"{int_field} deve essere un intero.")
            if not min_int <= val <= max_int:
                raise ValueError(f"{int_field} deve essere compreso tra {min_int} e {max_int}.")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class AudioDecodeError(RuntimeError):
    """Raised when an audio file cannot be decoded."""


def _dbfs(amplitude: float, floor_db: float = -120.0) -> float:
    if not np.isfinite(amplitude) or amplitude <= 0:
        return floor_db
    return max(floor_db, 20.0 * math.log10(float(amplitude)))


def _read_with_ffmpeg(data: bytes) -> tuple[np.ndarray, int]:
    """Decode formats not supported by the installed libsndfile via FFmpeg, if present."""
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise AudioDecodeError(
            "Formato non supportato da SoundFile. Per MP3 e altri formati, installa FFmpeg "
            "oppure converti il file in WAV/FLAC."
        )
    try:
        proc = subprocess.run(
            [ffmpeg, "-hide_banner", "-loglevel", "error", "-i", "pipe:0",
             "-vn", "-f", "wav", "-acodec", "pcm_f32le", "pipe:1"],
            input=data,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=45,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise AudioDecodeError("Timeout durante la decodifica FFmpeg.") from exc
    if proc.returncode != 0 or not proc.stdout:
        msg = proc.stderr.decode("utf-8", errors="replace")[-400:]
        raise AudioDecodeError(f"FFmpeg non è riuscito a decodificare il file. {msg}")
    try:
        audio, sr = sf.read(BytesIO(proc.stdout), dtype="float32", always_2d=True)
    except Exception as exc:
        raise AudioDecodeError(f"Impossibile leggere l'audio decodificato: {exc}") from exc
    return audio, int(sr)


def decode_audio(data: bytes) -> tuple[np.ndarray, int]:
    """Decode an audio byte buffer as float32 [frames, channels] and sample rate."""
    try:
        audio, sr = sf.read(BytesIO(data), dtype="float32", always_2d=True)
    except Exception:
        audio, sr = _read_with_ffmpeg(data)

    if audio.size == 0 or sr <= 0:
        raise AudioDecodeError("Audio file is empty or contains invalid metadata.")
    if not np.all(np.isfinite(audio)):
        raise AudioDecodeError("Audio buffer contains NaN or infinite values; analysis aborted for safety.")
    return np.asarray(audio, dtype=np.float32), int(sr)


def estimate_true_peak(audio: np.ndarray, sample_rate: int, factor: int = 4) -> tuple[float, float]:
    """Calculate true-peak level in linear amplitude and dBTP using ITU-R BS.1770-4 Annex 2 FIR.

    Uses upfirdn with the standardized 48-tap, 4-phase polyphase filter for factor=4.
    Guarantees true peak is never reported below discrete sample peak.
    """
    if audio.size == 0:
        return 0.0, -120.0

    abs_audio = np.abs(audio.astype(np.float64))
    sample_peak = float(np.max(abs_audio))

    factor = max(1, int(factor))
    if factor == 1 or audio.shape[0] == 0:
        return sample_peak, _dbfs(sample_peak)

    if factor == 4:
        oversampled = upfirdn(_BS1770_48TAP_FIR, audio.astype(np.float64), up=4, down=1, axis=0)
        tp_raw = float(np.max(np.abs(oversampled)))
    else:
        oversampled = resample_poly(audio.astype(np.float64), up=factor, down=1, axis=0)
        tp_raw = float(np.max(np.abs(oversampled)))

    true_peak = max(sample_peak, tp_raw)
    return true_peak, _dbfs(true_peak)


def detect_flat_top_clipping(audio: np.ndarray, threshold: float = 0.999, min_consecutive: int = 3) -> tuple[int, int]:
    """Detect digital flat-top clipping events and total flat-top samples."""
    if audio.size == 0:
        return 0, 0
    if audio.ndim == 1:
        audio = audio[:, np.newaxis]
    total_events = 0
    total_samples = 0
    for ch in range(audio.shape[1]):
        clipped = (np.abs(audio[:, ch]) >= threshold).astype(np.int8)
        if not np.any(clipped):
            continue
        diff = np.diff(np.pad(clipped, (1, 1), mode="constant"))
        starts = np.where(diff == 1)[0]
        ends = np.where(diff == -1)[0]
        run_lengths = ends - starts
        valid_runs = run_lengths[run_lengths >= min_consecutive]
        total_events += len(valid_runs)
        total_samples += int(np.sum(valid_runs))
    return total_events, total_samples


def calculate_stereo_correlation(
    audio: np.ndarray,
    sample_rate: int,
    silence_threshold_dbfs: float = -60.0,
    window_s: float = 0.2,
) -> tuple[float, float, float]:
    """Compute stereo Pearson phase correlation (avg and min) and mono drop in dB.

    Returns (avg_correlation, min_correlation, mono_drop_db).
    Mono signals return (1.0, 1.0, 0.0).
    """
    if audio.ndim != 2 or audio.shape[1] < 2:
        return 1.0, 1.0, 0.0

    left = audio[:, 0].astype(np.float64)
    right = audio[:, 1].astype(np.float64)
    n_samples = audio.shape[0]

    win_len = max(1, int(round(sample_rate * window_s)))
    n_wins = n_samples // win_len

    if n_wins > 0:
        trunc_len = n_wins * win_len
        l_mat = left[:trunc_len].reshape(n_wins, win_len)
        r_mat = right[:trunc_len].reshape(n_wins, win_len)

        l_pwr = np.mean(l_mat ** 2, axis=1)
        r_pwr = np.mean(r_mat ** 2, axis=1)
        thresh_sq = (10.0 ** (silence_threshold_dbfs / 20.0)) ** 2

        active = (l_pwr >= thresh_sq) | (r_pwr >= thresh_sq)
        if np.any(active):
            l_act = l_mat[active]
            r_act = r_mat[active]
            dot = np.sum(l_act * r_act, axis=1)
            denom = np.sqrt(np.sum(l_act ** 2, axis=1) * np.sum(r_act ** 2, axis=1))
            valid = denom > 1e-12
            if np.any(valid):
                rhos = np.clip(dot[valid] / denom[valid], -1.0, 1.0)
                avg_corr = float(np.mean(rhos))
                min_corr = float(np.min(rhos))
            else:
                avg_corr, min_corr = 1.0, 1.0
        else:
            avg_corr, min_corr = 1.0, 1.0
    else:
        avg_corr, min_corr = 1.0, 1.0

    mid = 0.5 * (left + right)
    e_mid = float(np.mean(mid ** 2))
    e_lr = float(0.5 * (np.mean(left ** 2) + np.mean(right ** 2)))

    if e_mid < 1e-12 and e_lr > 1e-12:
        mono_drop_db = 60.0
    elif e_mid > 1e-12 and e_lr > 1e-12:
        mono_drop_db = max(0.0, float(10.0 * math.log10(e_lr / e_mid)))
    else:
        mono_drop_db = 0.0

    return round(avg_corr, 2), round(min_corr, 2), round(mono_drop_db, 2)


def calculate_loudness_suite(
    audio: np.ndarray,
    sample_rate: int,
) -> dict[str, float | None]:
    """Calculate Integrated LUFS, Momentary Max LUFS, Short-Term Max LUFS, and LRA per ITU/EBU."""
    if pyln is None or audio.shape[0] < int(sample_rate * 0.4):
        return {
            "integrated_lufs": None,
            "momentary_max_lufs": None,
            "short_term_max_lufs": None,
            "loudness_range_lu": None,
        }

    try:
        meter = pyln.Meter(sample_rate)
        integrated = float(meter.integrated_loudness(audio))
        integrated_val = integrated if np.isfinite(integrated) else None

        m_blocks = getattr(meter, "blockwise_loudness", [])
        finite_m = [v for v in m_blocks if np.isfinite(v)]
        momentary_max = round(float(np.max(finite_m)), 2) if finite_m else None

        short_term_max = None
        if len(m_blocks) >= 30:
            kernel = np.ones(30, dtype=np.float64) / 30.0
            powers = np.array([10.0 ** (v / 10.0) if (np.isfinite(v) and v > -100.0) else 0.0 for v in m_blocks], dtype=np.float64)
            st_powers = np.convolve(powers, kernel, mode="valid")
            valid_st = st_powers[st_powers > 1e-12]
            if len(valid_st) > 0:
                st_lufs = 10.0 * np.log10(valid_st)
                short_term_max = round(float(np.max(st_lufs)), 2)
        elif momentary_max is not None:
            short_term_max = round(momentary_max, 2)

        lra_val = None
        if audio.shape[0] >= int(sample_rate * 3.0):
            try:
                lra = float(meter.loudness_range(audio))
                lra_val = round(lra, 2) if np.isfinite(lra) else None
            except Exception:
                lra_val = None

        return {
            "integrated_lufs": round(integrated_val, 2) if integrated_val is not None else None,
            "momentary_max_lufs": momentary_max,
            "short_term_max_lufs": short_term_max,
            "loudness_range_lu": lra_val,
        }
    except Exception:
        return {
            "integrated_lufs": None,
            "momentary_max_lufs": None,
            "short_term_max_lufs": None,
            "loudness_range_lu": None,
        }


def detect_silence_regions(
    audio: np.ndarray,
    sample_rate: int,
    threshold_dbfs: float = -60.0,
    min_duration_s: float = 0.25,
    frame_ms: float = 10.0,
) -> list[dict[str, float]]:
    """Detect near-silent regions using frame RMS over all channels.

    This is a practical QC heuristic, not speech/music-aware silence detection.
    Returned start/end times are rounded to milliseconds.
    """
    if audio.size == 0 or sample_rate <= 0:
        return []
    frame_len = max(1, int(round(sample_rate * frame_ms / 1000.0)))
    n_frames = int(math.ceil(audio.shape[0] / frame_len))
    padded_len = n_frames * frame_len
    pad = padded_len - audio.shape[0]
    x = np.pad(audio, ((0, pad), (0, 0))) if pad else audio
    frames = x.reshape(n_frames, frame_len, audio.shape[1])
    rms = np.sqrt(np.mean(np.square(frames, dtype=np.float64), axis=(1, 2)))
    threshold = 10.0 ** (threshold_dbfs / 20.0)
    silent = rms <= threshold
    min_frames = max(1, int(math.ceil(min_duration_s / (frame_len / sample_rate))))

    regions: list[dict[str, float]] = []
    start = None
    for i, flag in enumerate(silent):
        if flag and start is None:
            start = i
        if start is not None and (not flag or i == len(silent) - 1):
            end_frame_exclusive = i if not flag else i + 1
            length = end_frame_exclusive - start
            if length >= min_frames:
                start_s = start * frame_len / sample_rate
                end_s = min(end_frame_exclusive * frame_len / sample_rate, audio.shape[0] / sample_rate)
                regions.append({"start_s": round(start_s, 3), "end_s": round(end_s, 3), "duration_s": round(end_s - start_s, 3)})
            start = None
    return regions


def measure_edge_silence(
    audio: np.ndarray,
    sample_rate: int,
    threshold_dbfs: float = -60.0,
    search_duration_s: float = 10.0,
    window_ms: float = 5.0,
    hop_ms: float = 1.0,
) -> tuple[float, float]:
    """Measure leading and trailing silence with millisecond precision using windowed RMS.

    Searches the initial and final portions of the audio (up to search_duration_s).
    Returns (leading_silence_s, trailing_silence_s).
    """
    if audio.size == 0 or sample_rate <= 0:
        return 0.0, 0.0

    if audio.ndim == 1:
        audio = audio[:, np.newaxis]

    n_samples = audio.shape[0]
    total_duration_s = n_samples / sample_rate

    win_len = max(1, int(round(sample_rate * window_ms / 1000.0)))
    hop_len = max(1, int(round(sample_rate * hop_ms / 1000.0)))
    thresh_amp = 10.0 ** (threshold_dbfs / 20.0)
    thresh_sq = thresh_amp ** 2

    # Power per sample across all channels
    power = np.mean(np.square(audio, dtype=np.float64), axis=1)

    # 1. Leading silence
    lead_samples = min(n_samples, int(round(search_duration_s * sample_rate)))
    lead_power = power[:lead_samples]
    if lead_power.size >= win_len:
        kernel = np.ones(win_len, dtype=np.float64) / win_len
        mov_pwr = np.convolve(lead_power, kernel, mode="valid")[::hop_len]
        active_indices = np.where(mov_pwr >= thresh_sq)[0]
        if len(active_indices) > 0:
            first_active_sample = int(active_indices[0] * hop_len)
            leading_silence_s = first_active_sample / sample_rate
        else:
            leading_silence_s = min(total_duration_s, float(search_duration_s))
    else:
        leading_silence_s = 0.0 if np.any(lead_power >= thresh_sq) else total_duration_s

    # 2. Trailing silence
    trail_start_idx = max(0, n_samples - lead_samples)
    trail_power = power[trail_start_idx:]
    if trail_power.size >= win_len:
        kernel = np.ones(win_len, dtype=np.float64) / win_len
        mov_pwr = np.convolve(trail_power, kernel, mode="valid")[::hop_len]
        active_indices = np.where(mov_pwr >= thresh_sq)[0]
        if len(active_indices) > 0:
            last_active_sample = trail_start_idx + int(active_indices[-1] * hop_len) + win_len
            trailing_silence_s = max(0.0, (n_samples - last_active_sample) / sample_rate)
        else:
            trailing_silence_s = min(total_duration_s, float(search_duration_s))
    else:
        trailing_silence_s = 0.0 if np.any(trail_power >= thresh_sq) else total_duration_s

    return round(float(leading_silence_s), 3), round(float(trailing_silence_s), 3)


def analyze_audio(data: bytes, filename: str, settings: QCSettings | None = None) -> dict[str, Any]:
    """Compute audio metrics and QC checks for one file."""
    settings = settings or QCSettings()
    audio, sr = decode_audio(data)
    n_samples, channels = audio.shape
    duration_s = n_samples / sr
    audio_f64 = audio.astype(np.float64)
    abs_audio = np.abs(audio_f64)

    sample_peak = float(np.max(abs_audio)) if abs_audio.size else 0.0
    sample_peak_dbfs = _dbfs(sample_peak)

    # True Peak calculation via ITU-R BS.1770-4 48-tap polyphase filter
    factor = max(1, int(settings.oversampling_factor))
    true_peak_linear, true_peak_dbtp = estimate_true_peak(audio_f64, sr, factor=factor)

    # Clipping detection: both isolated full-scale samples and flat-top events (N >= 3)
    clip_samples = int(np.count_nonzero(abs_audio >= settings.clipping_threshold))
    total_channel_samples = int(audio.size)
    clip_percentage = 100.0 * clip_samples / max(1, total_channel_samples)
    flat_top_events, flat_top_samples = detect_flat_top_clipping(audio, threshold=settings.clipping_threshold, min_consecutive=3)

    # RMS level and Crest Factor
    rms_linear = math.sqrt(float(np.mean(np.square(audio_f64))))
    rms_dbfs = _dbfs(rms_linear)
    crest_factor_db = round(sample_peak_dbfs - rms_dbfs, 2)

    # DC offset
    channel_means = np.mean(audio_f64, axis=0)
    dc_offset_linear = float(np.max(np.abs(channel_means))) if channel_means.size else 0.0
    dc_offset_dbfs = _dbfs(dc_offset_linear)

    # Silence analysis
    regions = detect_silence_regions(
        audio, sr,
        threshold_dbfs=settings.silence_threshold_dbfs,
        min_duration_s=settings.min_silence_region_s,
    )
    leading_silence_s, trailing_silence_s = measure_edge_silence(
        audio, sr,
        threshold_dbfs=settings.silence_threshold_dbfs,
    )
    total_detected_silence_s = float(sum(r["duration_s"] for r in regions))

    # Stereo Correlation and Mono Compatibility
    stereo_corr_avg, stereo_corr_min, mono_drop_db = calculate_stereo_correlation(
        audio, sr,
        silence_threshold_dbfs=settings.silence_threshold_dbfs,
    )

    # Advanced Loudness Suite
    loudness = calculate_loudness_suite(audio, sr)
    lufs = loudness["integrated_lufs"]
    momentary_max = loudness["momentary_max_lufs"]
    short_term_max = loudness["short_term_max_lufs"]
    lra = loudness["loudness_range_lu"]

    checks: list[dict[str, str]] = []

    def add_check(name: str, status: str, value: str, detail: str) -> None:
        checks.append({"check": name, "status": status, "value": value, "detail": detail})

    # 1. Integrated Loudness
    if lufs is None:
        reason = "Loudness unavailable: signal too short (<400ms) or unsupported channel layout."
        add_check("Integrated Loudness", "WARN", "N/D", reason)
    else:
        delta = abs(lufs - settings.target_lufs)
        status = "PASS" if delta <= settings.lufs_tolerance else "FAIL"
        add_check(
            "Integrated Loudness", status, f"{lufs:.1f} LUFS",
            f"Target {settings.target_lufs:.1f} LUFS ± {settings.lufs_tolerance:.1f} LU."
        )

    # 2. Loudness Range (LRA) & Dynamics
    if lra is not None:
        lra_status = "PASS" if lra <= settings.max_lra_lu else "WARN"
        add_check(
            "Loudness Range (LRA)", lra_status, f"{lra:.1f} LU",
            f"Recommended ceiling {settings.max_lra_lu:.1f} LU (EBU Tech 3342 compliant)."
        )

    if momentary_max is not None:
        m_status = "PASS" if momentary_max <= settings.max_momentary_lufs else "WARN"
        add_check(
            "Max Momentary Loudness", m_status, f"{momentary_max:.1f} LUFS",
            f"Recommended ceiling {settings.max_momentary_lufs:.1f} LUFS (400ms sliding window)."
        )

    if short_term_max is not None:
        st_status = "PASS" if short_term_max <= settings.max_short_term_lufs else "WARN"
        add_check(
            "Max Short-Term Loudness", st_status, f"{short_term_max:.1f} LUFS",
            f"Recommended ceiling {settings.max_short_term_lufs:.1f} LUFS (3.0s sliding window)."
        )

    # 3. True Peak (BS.1770-4)
    tp_status = "PASS" if true_peak_dbtp <= settings.true_peak_ceiling_dbtp else "FAIL"
    tp_desc = f"Ceiling {settings.true_peak_ceiling_dbtp:.1f} dBTP; standard ITU-R BS.1770-4 {factor}× polyphase FIR filter."
    add_check("Estimated True Peak", tp_status, f"{true_peak_dbtp:.2f} dBTP", tp_desc)

    # 4. Digital Clipping (Flat-top N >= 3)
    ft_status = "PASS" if flat_top_samples <= settings.max_flat_top_samples else "FAIL"
    add_check(
        "Digital Flat-Top Clipping (N≥3)", ft_status, f"{flat_top_events} events ({flat_top_samples} samples)",
        "Sequences of 3 or more consecutive full-scale samples (digital DAC/ADC saturation)."
    )

    # 5. Full-scale sample count
    clip_status = "PASS" if clip_samples == 0 else "WARN"
    add_check(
        "Near Full-Scale Samples", clip_status, f"{clip_samples} ({clip_percentage:.4f}%)",
        f"Count of isolated samples with |x| ≥ {settings.clipping_threshold:.3f}."
    )

    # 6. Stereo Phase Correlation
    if channels >= 2:
        corr_status = "PASS" if stereo_corr_avg >= settings.min_phase_correlation else "FAIL"
        add_check(
            "Stereo Phase Correlation", corr_status, f"{stereo_corr_avg:.2f} (min: {stereo_corr_min:.2f})",
            f"Minimum threshold {settings.min_phase_correlation:.2f}; negative values cause mono cancellation."
        )

        mono_status = "PASS" if mono_drop_db <= settings.max_mono_drop_db else "WARN"
        add_check(
            "Mono Compatibility (Mono Drop)", mono_status, f"-{mono_drop_db:.1f} dB",
            f"Maximum tolerated attenuation {settings.max_mono_drop_db:.1f} dB in mono downmix (M = (L+R)/2)."
        )

    # 7. Edge Silence
    edge_silence_max = max(leading_silence_s, trailing_silence_s)
    silence_status = "PASS" if edge_silence_max <= settings.max_edge_silence_s else "FAIL"
    add_check(
        "Edge Silence (Head / Tail)", silence_status, f"{leading_silence_s:.2f}s / {trailing_silence_s:.2f}s",
        f"Limit per boundary {settings.max_edge_silence_s:.2f}s (5ms RMS precision)."
    )

    # 8. DC Offset
    dc_status = "PASS" if dc_offset_dbfs <= settings.dc_offset_limit_dbfs else "WARN"
    add_check(
        "DC Offset", dc_status, f"{dc_offset_dbfs:.1f} dBFS",
        f"Threshold {settings.dc_offset_limit_dbfs:.1f} dBFS; channel mean."
    )

    # 9. Dynamic Crest Factor
    crest_status = "PASS" if crest_factor_db >= 6.0 else "WARN"
    add_check(
        "Dynamic Range (Crest Factor)", crest_status, f"{crest_factor_db:.1f} dB",
        "Peak-to-RMS level ratio; values < 6 dB indicate heavy brickwall limiting or over-compression."
    )

    statuses = [c["status"] for c in checks]
    overall = "FAIL" if "FAIL" in statuses else ("WARN" if "WARN" in statuses else "PASS")

    return {
        "filename": filename,
        "status": overall,
        "duration_s": round(duration_s, 3),
        "sample_rate_hz": sr,
        "channels": channels,
        "integrated_lufs": lufs,
        "momentary_max_lufs": momentary_max,
        "short_term_max_lufs": short_term_max,
        "loudness_range_lu": lra,
        "sample_peak_dbfs": round(sample_peak_dbfs, 2),
        "estimated_true_peak_dbtp": round(true_peak_dbtp, 2),
        "clip_samples": clip_samples,
        "clip_percentage": round(clip_percentage, 6),
        "flat_top_events": flat_top_events,
        "flat_top_samples": flat_top_samples,
        "rms_dbfs": round(rms_dbfs, 2),
        "crest_factor_db": crest_factor_db,
        "dc_offset_dbfs": round(dc_offset_dbfs, 2),
        "leading_silence_s": round(leading_silence_s, 3),
        "trailing_silence_s": round(trailing_silence_s, 3),
        "total_detected_silence_s": round(total_detected_silence_s, 3),
        "stereo_correlation_avg": stereo_corr_avg,
        "stereo_correlation_min": stereo_corr_min,
        "mono_drop_db": mono_drop_db,
        "silence_regions": regions,
        "checks": checks,
        "settings": settings.to_dict(),
    }
