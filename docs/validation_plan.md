# AudioCheck — Real-World Audio Validation Framework

## Purpose

Empirically evaluate and cross-validate acoustic metrics and QC compliance rules on authentic recording, broadcasting, and mastering stems.

## Representative Test Matrix

Collect 10–20 authorized audio stems representing edge scenarios:

- Clean spoken dialogue and voice tracks with low-frequency acoustic rumble.
- Room tone, intentional pauses, and leading/trailing head/tail silence.
- Mono, mid-side, and wide stereo stems.
- Varied sampling rates (44.1 kHz, 48 kHz, 96 kHz) and bit depths (16-bit, 24-bit, 32-bit float).
- Low dynamic range hyper-compressed tracks, transient spikes, and analog/digital clipping.
- Extreme edge cases: short snippets (< 400 ms), truncated files, and lossy formats (MP3, AAC, OGG).

*Note: Do not commit proprietary client stems to public version control.*

## Metrological Verification Matrix

| Stem / File ID | Target Parameter | AudioCheck Engine | Reference Instrument (FFmpeg / EXPOSE) | Metrological Delta | Compliance Status |
|---|---|---:|---:|---:|---|
| stem_podcast_01 | Integrated Loudness | -16.02 LUFS | -16.0 LUFS | 0.02 LU | PASS |
| stem_podcast_01 | True Peak | -1.02 dBTP | -1.0 dBTP | 0.02 dB | PASS |
| stem_podcast_01 | Stereo Phase | +0.77 | +0.77 | 0.00 | PASS |

## Validation Acceptance Criteria

1. Align target thresholds with delivery specifications (e.g. EBU R128, AES TD1004, ACX/Audible).
2. Distinguish file decode errors from QC threshold violations: an unreadable stem yields exit code 3 (ERROR), while a failed threshold yields exit code 2 (FAIL).
3. Validate true peak interpolation with 4x polyphase FIR filtering against known synthetic and inter-sample overshoot signals.
4. Run regression benchmarks automatically across all commits via CI/CD test suites.
