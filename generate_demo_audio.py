"""Generate short synthetic WAV files for manual AudioCheck demos."""
from pathlib import Path
import numpy as np
import soundfile as sf

OUT = Path(__file__).parent / "examples"
OUT.mkdir(exist_ok=True)
SR = 48000
DURATION = 5.0
N = int(SR * DURATION)
t = np.arange(N, dtype=np.float64) / SR

# Clean 440 Hz tone, lower amplitude than full scale.
ok = (0.25 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)
sf.write(OUT / "01_clean_tone.wav", ok, SR, subtype="PCM_24")

# Sustained section over full scale: deliberately obvious sample clipping.
clipped = (1.15 * np.sin(2 * np.pi * 220 * t)).clip(-1.0, 1.0).astype(np.float32)
sf.write(OUT / "02_clipped_tone.wav", clipped, SR, subtype="PCM_16")

# 0.8 seconds of silence at both edges.
silence = np.zeros(int(0.8 * SR), dtype=np.float32)
mid = (0.18 * np.sin(2 * np.pi * 330 * t[:int(3.4 * SR)])).astype(np.float32)
edge_silence = np.concatenate([silence, mid, silence])
sf.write(OUT / "03_edge_silence.wav", edge_silence, SR, subtype="PCM_24")

# Low-level constant DC offset plus a small tone.
dc = (0.08 * np.sin(2 * np.pi * 550 * t) + 0.015).astype(np.float32)
sf.write(OUT / "04_dc_offset.wav", dc, SR, subtype="PCM_24")

# Low-level signal to trigger a loudness profile mismatch.
quiet = (0.003 * np.sin(2 * np.pi * 660 * t)).astype(np.float32)
sf.write(OUT / "05_quiet_tone.wav", quiet, SR, subtype="PCM_24")

print(f"Generated demo audio in {OUT}")
