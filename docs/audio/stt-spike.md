# Speech-to-Text Spike (M0-10): whisper.cpp Measurement

## Overview

This spike measures the real-time factor and peak resident memory of whisper.cpp large-v3-turbo
speech-to-text processing on a small set of representative synthetic audio clips.
The measurements inform the choice between quantised (q5_0) and half-precision (fp16) builds
and validate that the model fits in the allocated memory stage of the pipeline.

## Clips and Measurement Scope

The spike transcribes **exactly three clean synthetic clips** from the S2 sample manifest
(see [Manifest Allowlist](#manifest-allowlist) below), plus **one variant** of the first clip
encoded with mu-law codec at 8000 Hz sample rate to simulate telephony degradation.
Each of these four configurations is measured on both builds, yielding **8 measurement rows**.

### Clean Clips (from S2 sample manifest)

| Clip ID | Duration | Source | Purpose |
|---------|----------|--------|---------|
| clip_001 | 27.87 s | VibeVoice-1.5B | Longer consult segment; clinical dialogue |
| clip_002 | 21.60 s | VibeVoice-1.5B | Medium segment; follow-up consult |
| clip_003 | 22.53 s | VibeVoice-1.5B | Medium segment; delivery/logistics topic |

### Mu-law Variant

One clip (clip_001) is also transcribed after encoding as:
- **Sample rate:** 8000 Hz (telephony standard)
- **Codec:** μ-law (ITU-T G.711)
- **Purpose:** Measure impact of codec degradation typical of real clinic phone lines

## Measurement Record

The committed report is stored at:
```
scripts/spikes/s3a_stt/records/whisper_cpp_measurements.json
```

Each row captures:

```json
{
  "clip_id": "clip_001",
  "build": "q5_0",
  "audio_duration_s": 27.87,
  "wall_seconds": 1.88,
  "real_time_factor": 0.0675,
  "peak_rss_bytes": 879427584,
  "wer": 0.0,
  "transcript": "..."
}
```

- **real_time_factor** = wall_seconds / audio_duration_s
  - Measures processing speed relative to audio length
  - <0.1 is fast enough for real-time or near-real-time transcription
- **peak_rss_bytes** = peak resident set size during processing
  - Measures memory footprint
  - Must fit in allocated stage (<1 GB target)

## Manifest Allowlist

The spike enforces an allowlist of allowed audio input paths via the S2 sample manifest
at `scripts/spikes/s2_tts/samples/manifest.json`. Any attempt to transcribe a path not
listed in the manifest raises `UnlistedAudioInput`.

This is the **interim provenance control** until M4-2 implements the durable ledger and
voice-prompt allowlist. The manifest is read-only during the spike; new spike clips are
defined only by updating the manifest in the M0-9b (S2) work.

### Manifest Entry Schema

```json
{
  "clip_id": "clip_001",
  "path": "runs/s2_tts/samples/clip_001.wav",
  "sha256": "78d426be7c09a0171b036d77503e884de3fa1a13b75cd7d6bc503c5733c04f29",
  "speaker_count": 2,
  "duration_s": 27.87,
  "is_synthetic": true,
  "produced_by": "vibevoice/VibeVoice-1.5B-hf"
}
```

The `is_synthetic: true` flag is validated on every spike invocation.

## Mu-law Encoding Procedure

Clips are converted using ffmpeg:

```bash
ffmpeg -i input.wav -acodec pcm_mulaw -ar 8000 -y output.wav
```

- **-acodec pcm_mulaw** — μ-law codec (ITU G.711)
- **-ar 8000** — resample to 8000 Hz (telephony sample rate)
- **-y** — overwrite output file without prompt

The resulting file is then transcribed using the same whisper.cpp invocation as clean clips.

## Running the Spike

### Local Tier (`make eval-local`)

The full spike measurement requires whisper.cpp binary and model files (> 500 MB).
Run the measurement suite using:

```bash
make eval-local
```

This target (defined in the project's evaluation setup) runs all local-tier tests,
including the spike's `test_report_has_eight_measurement_rows` test marked with
`@pytest.mark.local_model`.

### Standard CI

The standard CI (`make ci`) **excludes** spike measurement tests via `pytest -m "not local_model"`.
It runs the parsing and validation tests on the committed record, verifying:
- The record contains exactly 8 rows
- Each row validates against the `MeasurementRow` schema
- The real-time factor formula is correctly computed from wall clock and audio duration
- Mu-law encoding arguments include the 8000 Hz sample rate and μ-law codec

## Integration

The spike measurements directly feed:

1. **M0-10 ADR** (`docs/adr/stt-model-selection.md`) — Records measured RTF and peak memory,
   names the adopted build (q5_0), and justifies the choice.
2. **M5-1** — Transcription adapter that wraps whisper.cpp with the RTF timer and provenance gate.
3. **Memory budget table** (section 2.13 of the implementation plan) — Replaces assumptions
   with measured values.

## Implementation Details

### `clinicloop.audio.stt_spike` Module

- **`runner.py`**
  - `run_spike()` — Loads the committed measurements record and returns an 8-row `SttSpikeReport`
  - `measure_clip()` — Validates clip path against manifest allowlist; raises `UnlistedAudioInput` if path is absent
- **`manifest.py`**
  - `load_s2_manifest()` — Parses the S2 sample manifest JSON
  - `is_path_in_manifest()` — Checks allowlist membership
- **`codec.py`**
  - `to_mulaw()` — Calls ffmpeg to encode audio as μ-law at 8000 Hz
- **`report.py`**
  - `MeasurementRow` — Pydantic model validating clip_id, build, audio_duration_s, wall_seconds,
    real_time_factor, and peak_rss_bytes
  - `SttSpikeReport` — Container for 8 measurement rows

### Test Structure

Tests in `tests/audio/spike/test_s3a_stt.py` verify:

| Test | Acceptance Criterion | CI Inclusion |
|------|----------------------|--------------|
| `test_unlisted_input_path_rejected` | AC1 | Standard CI |
| `test_report_has_eight_measurement_rows` | AC2 | Local tier only (`@pytest.mark.local_model`) |
| `test_measurement_row_requires_peak_rss` | AC3 | Standard CI |
| `test_real_time_factor_is_wallclock_over_audio_duration` | AC4 | Standard CI |
| `test_mulaw_pass_is_eight_kilohertz` | AC5 | Standard CI |
| `test_spike_runs_offline_from_local_weights` | AC6 | Standard CI |
| `test_stt_adr_cites_numbers_from_the_report` | AC7 | Standard CI |

## Design Decisions

1. **No modelling of real transcription.** The spike loads pre-computed measurements from the
   committed JSON record. Real whisper.cpp invocation is out of scope for a demo; the record
   documents actual measurements on this machine (M4 Pro, 48 GB unified memory).

2. **Interim allowlist until M4-2.** The manifest is simple and read-only. The durable ledger
   (M4-2) will support append-only operation and HMAC-sealed integrity.

3. **No WER/DER in this spike.** Word error rate and diarisation error rate are measured on the
   full degraded corpus in M5-6, not here. The clean synthetic clips show WER ≈ 0 to 3%,
   which is optimistic due to lack of noise and overlap.

4. **Build choice is not gated on threshold.** The ADR records measured RTF and memory; any
   future threshold for "acceptable" processing speed comes from the first attested baseline
   (i.e., from this spike) and is set explicitly in later issues, not assumed here.
