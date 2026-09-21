# ADR: Speech-to-Text Model Build Selection

## Status

Accepted

Date: 2026-09-21

Deciders: audiowright

## Context

The comprehension pipeline requires speech-to-text (STT) processing of synthetic phone consults.
Whisper.cpp large-v3-turbo is available in two builds: quantised (q5_0) and half-precision (fp16),
trading speed and memory against potential accuracy improvements.

The spike (M0-10) measures real-time factor and peak resident memory on three clean synthetic clips
and one mu-law-encoded clip using both builds, providing data to guide the adoption decision.

## Decision

Adopt the **q5_0 (quantised)** build of whisper.cpp large-v3-turbo for production use in the
comprehension pipeline.

### Rationale

The q5_0 build offers:
- **Real-time factor:** 0.076 (mean over 4 measurements: clean clips and mu-law variant)
- **Peak resident memory:** ~877 MB (mean peak RSS across measurements)

The fp16 build showed:
- **Real-time factor:** 0.091 (mean over 4 measurements)
- **Peak resident memory:** ~2009 MB (mean peak RSS across measurements)

The q5_0 build is ~20% faster and uses less than half the memory of fp16.
The measured word error rate on these clean synthetic clips is identical between builds (0.0–0.031),
but this represents an optimistic baseline using synthetic speech with no overlaps, background noise,
or telephony degradation. Real consult audio in M5-6 will measure WER on the full degraded corpus.

### Measured Values

The following values are derived from `scripts/spikes/s3a_stt/records/whisper_cpp_measurements.json`
and represent mean values across the spike's 4 measurement rows per build:

| Build | Mean RTF | Mean Peak RSS | Notes |
|-------|----------|---------------|-------|
| q5_0  | 0.076    | 877,657,688 bytes | Adopted |
| fp16  | 0.091    | 2,009,452,688 bytes | Alternative |

## Consequences

- The pipeline will use q5_0, satisfying the memory budget (<1 GB per stage).
- WER and diarisation error rate measurements on the full degraded corpus happen in M5-6 using the q5_0 build.
- If real consult WER on q5_0 shows unacceptable degradation, a retrial with fp16 is documented as rollback.
- Measured real-time factor (0.076) permits a 3-minute consult to transcribe in ~13.7 seconds, well within the pipeline's async processing window.

## Alternatives considered

- **fp16 (half-precision):** Higher memory cost (>2 GB) and slower processing provide no measured accuracy benefit on synthetic speech.
  WER measurement against the real degraded corpus will be done on q5_0; if fp16 is needed later, its RTF and memory are established.
