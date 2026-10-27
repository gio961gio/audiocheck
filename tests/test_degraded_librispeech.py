from pathlib import Path
import pytest

from scripts.run_degraded_librispeech_benchmark import (
    detect_waveform_plateaus,
    run_degraded_librispeech_benchmark,
)


def test_detect_waveform_plateaus_synthetic():
    import numpy as np

    # Clean sine wave: no plateau
    sr = 16000
    t = np.arange(sr) / sr
    clean = 0.5 * np.sin(2 * np.pi * 440 * t)
    events, samples, ratio = detect_waveform_plateaus(clean)
    assert events == 0
    assert samples == 0
    assert ratio == 0.0

    # Scaled clipped wave (clipped at 0.3 then turned down)
    clipped = np.clip(0.5 * np.sin(2 * np.pi * 440 * t), -0.3, 0.3)
    events, samples, ratio = detect_waveform_plateaus(clipped)
    assert events > 0
    assert samples > 0
    assert ratio > 0.10


def test_degraded_librispeech_benchmark_execution():
    root = Path(__file__).resolve().parent.parent
    ds_dir = root / "datasets" / "degraded_librispeech"

    if not ds_dir.exists() or not (ds_dir / "ground_truth.json").exists():
        pytest.skip("Dataset Degraded LibriSpeech non presente localmente")

    summary = run_degraded_librispeech_benchmark()
    assert summary["metrics"]["accuracy"] >= 0.95
    assert summary["metrics"]["precision"] >= 0.95
    assert summary["metrics"]["f1_score"] >= 0.95
    assert summary["confusion_matrix"]["false_positives"] == 0
