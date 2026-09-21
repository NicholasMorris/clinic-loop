# Text-to-Speech Spike S2: Measurement Results

## Summary

This spike measures text-to-speech synthesis performance on Apple Silicon (M4 Pro, 48 GB unified memory) to determine the feasible audio generation strategy. The measurements use VibeVoice-1.5B-hf, a 1.5 billion parameter model with per-turn synthesis capability.

## Measured Report

The following values are derived from the spike measurement records and committed to `scripts/spikes/s2_tts/report.json`:

| Metric | Value |
|--------|-------|
| Real-time factor (RTF) | 1.055 |
| Peak RSS memory | 7.2 GB |
| Render time (3 minutes) | 189.9 seconds |
| Disclaimer occurrences per generation | 0 |
| Disclaimer offset (seconds) | 0.0 |
| Disclaimer duration (seconds) | 0.0 |
| Disclaimer excludable | true |
| Per-turn samples | 6 |
| Measured sample duration | 72.0 seconds |

## Branch Selection

**Branch B: Per-turn synthesis**

The branching rule (from `clinicloop.audio.spike.branch.select_branch`) applies decision thresholds:
- Branch C triggers if RTF > 3.0 or 3-minute render time > 600 seconds
- Branch A triggers if disclaimer repeats per generation and is not excludable
- Branch B (default) when metrics permit

With RTF = 1.055 and render time = 189.9 seconds, neither threshold is exceeded. The disclaimer was found in zero of four checked clips (method: Whisper-small.en transcript search), so no exclusion is needed. **Branch B is selected**, permitting per-turn synthesis and exact ground truth by construction.

## Sample Manifest

Three synthetic sample clips are preserved in the spike scratch directory `runs/s2_tts/samples/` (gitignored). The manifest is committed to `scripts/spikes/s2_tts/samples/manifest.json`:

- **clip_001.wav**: 27.87 seconds, speakers 6097 (Phil Benson) and 17483 (Laurie Banza)
- **clip_002.wav**: 21.60 seconds, speakers 3906 (tabithat) and 13963 (Brianna Chiles)
- **clip_003.wav**: 22.53 seconds, speakers 6097 (Phil Benson) and 13963 (Brianna Chiles)

All clips are marked `is_synthetic: true` and carry SHA-256 hashes for provenance. Produced by: `vibevoice/VibeVoice-1.5B-hf`.

## Corpus Size

The frozen corpus target is **40 consults**, as specified in the measurement requirements. This size is derived from the M0-9a spike harness baseline; the actual corpus will be generated deterministically by seed in the M4-3 production text-to-speech worker.

## Disclaimer Treatment

The disclaimer is **not removed**: it is kept in synthesis output and excluded from word error rate and diarisation error rate calculations by a fixed rule in the evaluation harness (documented in `docs/evaluation.md`). The measurements show:
- Disclaimer phrase presence: 0 occurrences in 4 checked clips
- Method: Whisper-small.en transcript search
- No imperceptible watermark was verified; audio is marked synthetic by the project's provenance layer (M4-2)

## Open Item

USER: Listen to the three sample clips in `runs/s2_tts/samples/` and confirm the accent sounds Australian.
