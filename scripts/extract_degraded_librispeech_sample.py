"""Extract a balanced sample from Degraded LibriSpeech (Zenodo 8380442).

Selects 20 clean utterances and 25 clipped utterances (5 files across each
clipping intensity: 5%, 10%, 25%, 40%, 60%), generating the ground truth manifest
with SHA-256 hashes and controlled_transform_label taxonomy.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tarfile


def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def extract_sample() -> dict:
    root = Path(__file__).resolve().parent.parent
    target_dir = root / "datasets" / "degraded_librispeech"
    target_dir.mkdir(parents=True, exist_ok=True)

    clean_bin = root / "datasets" / "temp_clean_head.bin"
    nomad_bin = root / "datasets" / "temp_nomad_head.bin"

    manifest = {}

    # 1. Extract 20 Clean Files
    clean_count = 0
    if clean_bin.exists():
        with tarfile.open(clean_bin, "r:gz") as tar:
            for member in tar:
                if member.isfile() and member.name.endswith(".wav"):
                    dest_name = f"clean_{Path(member.name).name}"
                    dest_path = target_dir / dest_name
                    with tar.extractfile(member) as src, open(dest_path, "wb") as dst:
                        dst.write(src.read())

                    manifest[dest_name] = {
                        "dataset": "Degraded LibriSpeech / clean_ls (Zenodo 8380442)",
                        "condition": "clean",
                        "clipping_intensity_pct": 0,
                        "expected_has_clipping": False,
                        "ground_truth_type": "controlled_transform_label",
                        "audio_sha256": compute_sha256(dest_path),
                        "description": "Clean speech reference from LibriSpeech (public domain audiobooks)",
                    }
                    clean_count += 1
                    if clean_count >= 20:
                        break

    # 2. Extract 25 Clipped Files (5 per percentage: 5, 10, 25, 40, 60)
    desired_levels = {5: 5, 10: 5, 25: 5, 40: 5, 60: 5}
    collected_levels = {k: 0 for k in desired_levels}

    if nomad_bin.exists():
        with tarfile.open(nomad_bin, "r:gz") as tar:
            for member in tar:
                if not member.isfile() or not member.name.endswith(".wav"):
                    continue

                fname = Path(member.name).name
                # Filename pattern: ..._CLIP_<pct>.wav
                for lvl in desired_levels:
                    if f"_CLIP_{lvl}.wav" in fname and collected_levels[lvl] < desired_levels[lvl]:
                        dest_name = f"clip_{lvl}pct_{fname}"
                        dest_path = target_dir / dest_name
                        with tar.extractfile(member) as src, open(dest_path, "wb") as dst:
                            dst.write(src.read())

                        manifest[dest_name] = {
                            "dataset": "Degraded LibriSpeech / nomad_ls (Zenodo 8380442)",
                            "condition": f"clipping_{lvl}pct",
                            "clipping_intensity_pct": lvl,
                            "expected_has_clipping": True,
                            "ground_truth_type": "controlled_transform_label",
                            "audio_sha256": compute_sha256(dest_path),
                            "description": f"Controlled waveform clipping at {lvl}% of samples (Alessandro Ragano et al.)",
                        }
                        collected_levels[lvl] += 1
                        break

                if all(collected_levels[k] >= desired_levels[k] for k in desired_levels):
                    break

    # Save manifest
    gt_file = target_dir / "ground_truth.json"
    gt_file.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Estratti {clean_count} file clean e {sum(collected_levels.values())} file clipped:")
    for lvl, count in collected_levels.items():
        print(f"  - Clipping {lvl}%: {count} file")
    print(f"Manifest ground truth salvato in: {gt_file}")

    # Remove temporary bin archives to free space
    if clean_bin.exists():
        clean_bin.unlink()
    if nomad_bin.exists():
        nomad_bin.unlink()

    return manifest


if __name__ == "__main__":
    extract_sample()
