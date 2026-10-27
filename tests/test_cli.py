import csv
import json
from pathlib import Path
import pytest

from audiocheck_cli import main


def test_cli_help(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--help"])
    assert exc.value.code == 0
    captured = capsys.readouterr()
    assert "AudioCheck CLI" in captured.out


def test_cli_no_inputs(capsys):
    code = main([])
    assert code == 3


def test_cli_missing_input_returns_error_code_3(capsys):
    code = main(["file_that_definitely_does_not_exist_12345.wav", "--quiet"])
    assert code == 3


def test_cli_corrupted_file_returns_error_code_3(tmp_path, capsys):
    corrupt_file = tmp_path / "corrupt.wav"
    corrupt_file.write_bytes(b"NOT_A_VALID_WAV_HEADER_DATA")

    code = main([str(corrupt_file), "--quiet"])
    assert code == 3


def test_cli_mixed_batch_valid_and_corrupt_returns_error_code_3(tmp_path, capsys):
    root = Path(__file__).resolve().parent.parent
    clean_wav = root / "examples" / "01_clean_tone.wav"
    corrupt_file = tmp_path / "corrupt_mixed.wav"
    corrupt_file.write_bytes(b"INVALID_HEADER_GARBAGE")

    code = main([str(clean_wav), str(corrupt_file), "--quiet"])
    # Decode errors must not be masked by passing files; should yield 3 (ERROR)
    assert code == 3


def test_cli_run_on_examples(tmp_path, capsys):
    root = Path(__file__).resolve().parent.parent
    examples_dir = root / "examples"

    code = main([
        str(examples_dir),
        "--preset", "podcast",
        "--out-dir", str(tmp_path),
        "--format", "html,json,csv",
    ])
    # The synthetic examples contain clipped and quiet tones, so exit code should be 2 (FAIL)
    assert code == 2

    assert (tmp_path / "audiocheck_report.html").exists()
    assert (tmp_path / "audiocheck_report.json").exists()
    assert (tmp_path / "audiocheck_report.csv").exists()

    data = json.loads((tmp_path / "audiocheck_report.json").read_text(encoding="utf-8"))
    assert data["exit_code"] == 2
    assert data["summary"]["total_files"] == 5

    # Check that CSV parsed correctly
    with open(tmp_path / "audiocheck_report.csv", encoding="utf-8-sig") as f:
        reader = list(csv.DictReader(f))
        assert len(reader) == 5
        assert any(row["Status"] == "FAIL" for row in reader)


def test_cli_json_mode_pure_stdout_no_disk_side_effects(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    root = Path(__file__).resolve().parent.parent
    clean_wav = root / "examples" / "01_clean_tone.wav"

    code = main([
        str(clean_wav),
        "--preset", "podcast",
        "--json",
        "--quiet",
    ])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["summary"]["total_files"] == 1
    assert "01_clean_tone.wav" in data["results"][0]["filename"]
    assert "integrated_lufs" in data["results"][0]

    # Verify no files were created on disk in pure stdout --json mode
    created_files = list(tmp_path.glob("*"))
    assert len(created_files) == 0


def test_cli_json_mode_with_explicit_format(tmp_path, capsys):
    root = Path(__file__).resolve().parent.parent
    clean_wav = root / "examples" / "01_clean_tone.wav"

    code = main([
        str(clean_wav),
        "--preset", "podcast",
        "--json",
        "--out-dir", str(tmp_path),
        "--format", "json,html",
    ])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["summary"]["total_files"] == 1

    # Verify explicit format created the files
    assert (tmp_path / "audiocheck_report.json").exists()
    assert (tmp_path / "audiocheck_report.html").exists()
    assert not (tmp_path / "audiocheck_report.csv").exists()
