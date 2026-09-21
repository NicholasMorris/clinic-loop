# Text-to-Speech Spike Harness

The text-to-speech (S2) spike harness measures the performance characteristics of the VibeVoice TTS worker and applies decision rules to select the audio generation strategy. This harness is pure and testable; all measurements and branching logic run offline against fixture reports.

## Measured Fields

The `SpikeReport` pydantic model captures the following measurements:

- `real_time_factor`: Real-time factor for TTS processing (lower is better)
- `peak_rss_bytes`: Peak resident set size in bytes
- `disclaimer_offset_s`: Position of the synthetic-audio disclaimer in seconds
- `disclaimer_duration_s`: Duration of the disclaimer segment in seconds
- `disclaimer_occurrences_per_generation`: Number of times the disclaimer is heard per complete generation
- `disclaimer_excludable`: Whether the disclaimer can be excluded from output
- `three_minute_render_seconds`: Time to render a 3-minute consult in seconds (total wall-clock)
- `corpus_size`: Size of the audio corpus built during the spike
- `per_turn_samples`: Number of samples per conversation turn
- `measured_sample_duration_s`: Duration of the measured audio samples in seconds

## Branching Rules

The `select_branch(report)` function applies the following decision logic:

### Branch C: Limited Corpus
- Applies when `real_time_factor > 3.0` OR `three_minute_render_seconds > 600`
- Strategy: Use a smaller frozen corpus with shorter consults (60–90 seconds)
- Rationale: Performance thresholds exceeded; reduced throughput acceptable

### Branch A: Whole-Dialogue + Forced Alignment
- Applies when `disclaimer_occurrences_per_generation > 1` AND `disclaimer_excludable == False`
- Strategy: Generate one audio file per entire dialogue; use forced alignment (M4-6) to derive ground truth for turn-level boundaries
- Rationale: Per-turn synthesis would repeat the disclaimer audibly; alignment-derived truth trades per-sample accuracy for acceptability
- Requires: M4-6 (forced aligner) built first if S2 selects Branch A

### Branch B: Per-Turn Synthesis (Default)
- Applies when metrics permit (RTF ≤ 3.0, 3-min render ≤ 600, disclaimer avoidable or occurs at most once per generation)
- Strategy: Generate one audio file per conversation turn; assemble into a dialogue with known turn offsets
- Rationale: Exact ground truth by construction; preferred for accuracy
- Boundary values: RTF **exactly 3.0** and 3-min render **exactly 600** both select Branch B

## Isolated Environment Invocation

The `run_isolated_worker()` function invokes the TTS worker in a completely isolated `uv` environment:

```bash
uv run --no-project --offline <fork-commit> <transformers-version>
```

Where:
- `<fork-commit>`: Pinned fork commit from `scripts/spikes/s2_tts/pins.toml`
- `<transformers-version>`: Pinned transformers version from `pins.toml`
- `--offline` flag: Ensures no network access during execution
- `--no-project` flag: Worker runs without inheriting project dependencies

The worker accepts optional input audio paths. Any input audio must have been produced by this worker run itself; audio from other sources raises `NonSpikeAudioInput` with the rejected path in the error message.

## Pin File

The `scripts/spikes/s2_tts/pins.toml` file records the exact versions used:

```toml
[pins]
fork_commit = "..."  # Specific fork commit SHA
transformers_version = "4.30.0"  # Exact transformers version
```

This ensures that spike measurements are reproducible across machines and time.

## Manifest Entry Schema

Each audio clip in the spike is recorded in a manifest with the following fields:

- `clip_id`: Unique identifier for the clip
- `path`: File path relative to `runs/s2_tts/samples/`
- `sha256`: SHA-256 hash of the audio bytes
- `speaker_count`: Number of speakers in the clip
- `duration_s`: Duration in seconds
- `is_synthetic`: Always `True` for spike audio (enforced at validation)
- `produced_by`: Name of the worker that produced the clip

The manifest serves as interim provenance control until M4-2 (ledger and voice-prompt allowlist) is implemented. Every clip must include its SHA-256 hash, and non-synthetic audio is rejected at validation time.

## Audio Output

Spike audio clips are written to the gitignored directory:

```
runs/s2_tts/samples/
```

These are **throwaway artifacts** that do not enter the production corpus. They are discarded after the spike; any clips reused in later work are re-registered in the M4-2 ledger.

The `write_sample()` function writes worker output bytes to disk unchanged. The SHA-256 of the written file is compared against the hash of the input bytes. If any alteration is detected, `DisclaimerAudioAltered` is raised and the file is removed from disk, ensuring that the manifest never records corrupted audio.

## Interim Provenance Control

Until M4-2 (ledger and voice-prompt allowlist) is implemented, provenance for spike audio relies on:

1. **Manifest with SHA-256 hashes**: Every spike clip records its hash; corrupted audio is detected and rejected
2. **Worker refusal**: The worker refuses to process audio it did not produce, enforced via `NonSpikeAudioInput`

This is a **tamper-evident control on a single machine**, not a cryptographic security boundary. The README documents this limitation and states that spike audio is for development and measurement only.

## Voice Prompts

The voice prompts used for TTS are public recordings with Australian English accent from a permissively licensed speech corpus. Their SHA-256 values:

- Are recorded in the spike manifest
- Become the starting allowlist inherited by M4-2
- Allow downstream code to verify that only expected reference clips were used

## Future Work

- **M0-9b**: Architectural decision records for audio generation strategy selection
- **M4-2**: Production ledger, HMAC sidecar, and voice-prompt allowlist
- **M4-3**: Production text-to-speech worker in isolated environment
- **M5-6**: Evaluation metrics showing how the disclaimer is excluded from WER/DER calculations
