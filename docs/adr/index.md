# Architecture Decision Records

This section contains the Architecture Decision Records (ADRs) for ClinicLoop.
Each ADR documents a significant decision made during development, including the context,
decision rationale, consequences, and alternatives considered.

## ADR Registry

The following ADRs are planned or completed:

1. **llm-model-selection** — Selection of LLM model(s) and inference strategy
2. **tts-engine-and-pin** — Text-to-speech engine and voice configuration
3. **stt-model-selection** — Speech-to-text model selection
4. **diarisation-approach** — Speaker diarisation strategy and implementation
5. **terminology-edition** — Clinical terminology edition and mapping approach
6. **human-gates** — Human-in-the-loop approval and review gates
7. **checkpointing** — Agent state checkpointing and persistence strategy
8. **framework-choice** — LangGraph and framework architecture decisions
9. **model-tiers-and-review** — Model tier classification and review processes
10. **ci-tiers-and-recorded-results** — CI tier definitions and result recording
11. **sandbox-limits** — Sandbox security model and resource constraints
12. **integrity-allowlist** — Integrity signal allowlist design and implementation

## Reading an ADR

Each ADR follows this template:

- **Status** — Current state of the decision (Proposed/Accepted/Deprecated/Superseded)
- **Context** — The problem or issue motivating the decision
- **Decision** — The decision made and its rationale
- **Consequences** — Trade-offs and implications
- **Alternatives considered** — Other options evaluated and why they were rejected
