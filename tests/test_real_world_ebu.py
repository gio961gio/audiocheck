from pathlib import Path
import pytest

from scripts.run_real_world_benchmark import run_real_world_benchmark


def test_real_world_ebu_programme_simulation_accuracy():
    root = Path(__file__).resolve().parent.parent
    real_dir = root / "datasets" / "ebu_real_world"

    # Skip if dataset not extracted locally
    if not real_dir.exists() or not list(real_dir.glob("*.wav")):
        pytest.skip("Dataset reale EBU non presente in datasets/ebu_real_world")

    summary = run_real_world_benchmark()
    assert summary["accuracy_pct"] == 100.0
    assert summary["passed_checks"] == summary["total_checks"]
    assert summary["total_checks"] == 9
