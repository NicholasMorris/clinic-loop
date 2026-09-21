# ADR: Text-to-Speech Engine and Version Pins

## Status

Accepted

## Context

The clinic-loop project requires deterministic, offline text-to-speech synthesis for reproducible synthetic phone consults. The engine must run on Apple Silicon, integrate with LangGraph pipelines, and produce audio with controlled acoustic properties (speaker selection, accent, rate, noise degradation).

## Decision

Use the native transformers implementation of VibeVoice-1.5B-hf (MIT licence) with pinned versions:
- `transformers` 5.17.0
- `torch` 2.14.0
- `diffusers` 0.40.0
- Model: `vibevoice/VibeVoice-1.5B-hf`

The model is loaded via `AutoModelForTextToWaveform` (native in transformers, no fork required). The inference environment is isolated from the repository via `uv venv` to ensure reproducibility and offline operation.

## Rationale

### Model Capability

VibeVoice-1.5B is a text-to-waveform model designed for speech synthesis. Quoted from the public model card:

- **Maximum speakers:** 4 (2 used in this project for clinician + patient roles)
- **Language support:** English and Chinese
- **Input:** Text and reference voice clip (24 kHz audio)
- **Output:** Speech-only (no noise or overlapping speech)
- **Speed control:** Not available; rate variations are applied post-synthesis via degradation layer
- **Accent:** Derived from reference voice prompt
- **Licence:** MIT

### Voice Reference Clips

The project uses public, permissively licensed LibriVox recordings as voice reference prompts. These are sourced from the Hugging Face community dataset `ablmontazer/australian-english-speech` (licence: CC0-1.0). The dataset card states:

- Recordings are volunteer donations to the public domain
- Accent is not verified per reader (ground truth limitation)
- A minority of narrators reading Australian books are not themselves Australian

All output audio is marked synthetic in metadata (via the project's provenance layer, M4-2). Accent guidance is noted as Australian-English per voice reader labels in the dataset.

### Disclaimer and Watermarks

The model card indicates the inference code embeds:
1. An **audible AI disclaimer** (kept in output; excluded from ASR metrics)
2. An **inaudible watermark** (not verified in this measurement)

The spike measurement (S2) checked 4 clips for disclaimer phrases using Whisper-small.en; none were detected. The absence of a detected audible disclaimer may indicate the phrase is present but not captured by the ASR model, or not present in these particular runs. The project marks all output as synthetic regardless.

### Transformers Integration

AutoModelForTextToWaveform is natively available in transformers 5.17.0. Microsoft's official VibeVoice-TTS repository was removed for responsible-use reasons; the transformers port is the active, publicly available implementation.

## Alternatives considered

1. **PyTorch direct implementation**: Increases maintenance burden; transformers integration is standard.
2. **Kokoro-82M or Piper**: Smaller, faster models; not evaluated against the clinic-loop requirements in S2. Could be revisited in future spikes.
3. **Cloud-based TTS**: Violates offline-only constraint (L1, L6).

## Consequences

- Speech synthesis RTF ~1.055 permits per-turn generation (Branch B)
- Memory usage ~7.2 GB (fits 48 GB tier; compatible with LLM stage isolation)
- Voice prompts must be CC0-licensed or equivalent; attribution in docs is required
- Offline operation is guaranteed; no remote calls or credentials needed
- The GPL/commercial licensing of some TTS alternatives is avoided

## Implementation

Version pins are recorded in `scripts/spikes/s2_tts/pins.toml`. The M4-3 production worker reuses these pins and validates against them at startup.
