"""Render terminal showcase card for README."""
from pathlib import Path
import time
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = ROOT / "assets"

terminal_html = """<!doctype html>
<html>
<head>
<meta charset="utf-8">
<style>
body {
    margin: 0;
    padding: 30px;
    background: #0d1117;
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
    color: #e6edf3;
}
.term-window {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 10px;
    max-width: 900px;
    margin: 0 auto;
    box-shadow: 0 12px 32px rgba(0,0,0,0.6);
    overflow: hidden;
}
.term-bar {
    background: #21262d;
    padding: 10px 16px;
    display: flex;
    align-items: center;
    gap: 8px;
    border-bottom: 1px solid #30363d;
}
.dot { width: 12px; height: 12px; border-radius: 50%; }
.dot-red { background: #ff5f56; }
.dot-yellow { background: #ffbd2e; }
.dot-green { background: #27c93f; }
.term-title {
    margin-left: 12px;
    font-size: 12px;
    color: #8b949e;
    font-weight: 600;
}
.term-body {
    padding: 18px 22px;
    font-size: 13px;
    line-height: 1.6;
}
.cmd { color: #58a6ff; font-weight: 700; }
.dim { color: #8b949e; }
.green { color: #3fb950; font-weight: 700; }
.yellow { color: #d29922; font-weight: 700; }
.red { color: #f85149; font-weight: 700; }
.cyan { color: #38bdf8; }
.bold { font-weight: 700; }
</style>
</head>
<body>
<div class="term-window">
    <div class="term-bar">
        <div class="dot dot-red"></div>
        <div class="dot dot-yellow"></div>
        <div class="dot dot-green"></div>
        <div class="term-title">bash — audiocheck --preset podcast examples/</div>
    </div>
    <div class="term-body">
        <div><span class="dim">$</span> <span class="cmd">python audiocheck_cli.py</span> <span class="cyan">examples/</span> <span class="dim">--preset podcast -o ./reports</span></div>
        <div class="dim">====================================================================</div>
        <div class="bold cyan">         AUDIOCHECK — BATCH AUDIO QUALITY CONTROL ENGINE</div>
        <div class="dim">====================================================================</div>
        <div>Active Profile : <span class="bold">Podcast &amp; Streaming (AES TD1004 / Spotify / Apple)</span></div>
        <div>Target Loudness: -16.0 LUFS (±1.5 LU)</div>
        <div>True Peak Max  : -1.0 dBTP (ITU-R BS.1770-4 4x FIR)</div>
        <div>LRA Max        : 12.0 LU</div>
        <div class="dim">====================================================================</div>
        <br>
        <div class="dim">---------------------------------------------------------------------------</div>
        <div class="bold">STATUS | FILE                         | LUFS     | TRUE PEAK  | LRA    | CORR </div>
        <div class="dim">---------------------------------------------------------------------------</div>
        <div><span class="green">PASS  </span> | 01_clean_tone.wav            | -16.0    | -3.01      | 0.0    | Mono </div>
        <div><span class="yellow">WARN  </span> | 02_stereo_phase_issue.wav    | -16.0    | -3.01      | 0.0    | <span class="red">-0.82</span></div>
        <div><span class="red">FAIL  </span> | 03_harsh_clipped.wav         | -8.4     | <span class="red">+1.85</span>     | 3.1    | Mono </div>
        <div><span class="red">FAIL  </span> | 04_excessive_silence.wav     | -16.0    | -3.01      | 0.0    | Mono </div>
        <div><span class="yellow">WARN  </span> | 05_high_dc_offset.wav        | -16.0    | -3.01      | 0.0    | Mono </div>
        <div class="dim">---------------------------------------------------------------------------</div>
        <div>SUMMARY: 5 evaluated · <span class="green">PASS: 1</span> · <span class="yellow">WARN: 2</span> · <span class="red">FAIL: 2</span> · ERROR: 0</div>
        <div>OVERALL OUTCOME: <span class="red">FAIL</span> (Exit code: 2)</div>
        <br>
        <div class="green">[OK] HTML report saved to: ./reports/audiocheck_report.html</div>
        <div class="green">[OK] JSON report saved to: ./reports/audiocheck_report.json</div>
        <div class="green">[OK] CSV report saved to : ./reports/audiocheck_report.csv</div>
    </div>
</div>
</body>
</html>"""

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        temp_html = ASSETS_DIR / "temp_term.html"
        temp_html.write_text(terminal_html, encoding="utf-8")
        page.set_viewport_size({"width": 960, "height": 620})
        page.goto(f"file:///{temp_html.as_posix()}")
        page.wait_for_load_state("networkidle")
        time.sleep(0.5)
        out_path = ASSETS_DIR / "cli_batch_showcase.png"
        page.screenshot(path=str(out_path))
        temp_html.unlink(missing_ok=True)
        browser.close()
        print(f"Captured CLI showcase to {out_path}")

if __name__ == "__main__":
    main()
