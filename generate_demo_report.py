"""Generate an HTML report from the bundled synthetic WAV examples."""
from pathlib import Path

from audiocheck_core import QCSettings, analyze_audio
from profiles import BUILT_IN_PROFILES
from reporting import build_html_report


def main() -> None:
    root = Path(__file__).resolve().parent
    examples_dir = root / "examples"
    audio_files = sorted(examples_dir.glob("*.wav"))
    if not audio_files:
        raise SystemExit("Nessun WAV trovato in examples/. Esegui prima generate_demo_audio.py.")

    profile_name = "Podcast & Streaming (AES TD1004 / Spotify / Apple)"
    settings = QCSettings(**BUILT_IN_PROFILES[profile_name]["settings"])
    results = [analyze_audio(path.read_bytes(), path.name, settings) for path in audio_files]
    report = build_html_report(results, [], settings.to_dict(), profile_name)
    output = root / "demo_report.html"
    output.write_text(report, encoding="utf-8")
    print(f"Report successfully generated at: {output}")


if __name__ == "__main__":
    main()
