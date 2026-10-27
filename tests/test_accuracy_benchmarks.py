import json
from pathlib import Path
import pytest

from scripts.generate_ground_truth_dataset import generate_dataset
from scripts.run_accuracy_benchmark import run_benchmark


def test_accuracy_ground_truth_suite():
    root = Path(__file__).resolve().parent.parent
    gt_path = root / "datasets" / "ebu_compliance" / "ground_truth.json"

    if not gt_path.exists():
        generate_dataset()

    summary = run_benchmark()
    assert summary["accuracy_pct"] == 100.0
    assert summary["total_checks"] == 30
    assert summary["passed_checks"] == 30
    assert summary["failed_checks"] == 0
    assert summary["speed_factor_realtime"] > 5.0
