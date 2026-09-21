# Requirement checklist (traceability source)

## Product
- B1 Public repo github.com/NicholasMorris/<neutral-name>, Python 3.12. Suggest three names. NOT named after target company.
- B2 One system, five components sharing one synthetic world:
  - C0 SimClinic: telehealth sim; synthetic patients on a clock; intake queue, prescriber queue, pharmacy fulfilment queue, support inbox; deterministic given a seed; dashboard with throughput, median wait, SLA breaches, cost per order; toggle each agent off and watch queues back up.
  - C1 Triage agent: reads inbound patient messages, resolves what is safe, drafts replies for human approval, hard-escalates the rest; every draft passes a pre-send rule check; blocked drafts route to a human citing the specific rule.
  - C2 Automation Factory: operator describes manual process in plain English; agent interviews; emits structured spec incl. explicit "do not automate" section; writes failing tests from acceptance criteria; implements until green against SimClinic mock APIs; reports measured impact; emits handover folder.
  - C3 Integrity agent: flags applications for human clinical review (see hard constraints).
  - C4 Consult audio pipeline: (a) generation: two-speaker synthetic phone consults from SimClinic patient records; varied accents, speech rates, interruptions, background noise, degraded telephony audio; reproducible from a seed. (b) comprehension: LangGraph agent that transcribes, diarises, produces structured consult note, action items, missing-information prompts, coded terms mapped to SNOMED CT-AU and ICD-10-AM; draft for clinician sign-off only; per-field confidence; below threshold flagged, never guessed.
  - Loop closure: transcripts feed triage (follow-up messages reference the call) and integrity (questionnaire text contradicting what was said aloud is a review signal, not an accusation).

## Grounding
- G1 Confirmed facts: 3-step flow (questionnaire -> clinician review -> if approved partner pharmacy dispenses and ships); free initial and follow-up consults; no referral; phone consults booked online; monthly plan, cancel anytime; flat $9.95 shipping under $129, free above; discreet packaging; LiveChat; clinic handles appointments and applications on behalf; AU/NZ/UK three regimes; job ad 90-day order: patient support, clinic and prescriber ops, pharmacy order ops.
- G2 Fetch the site for more. Derive >= 12 recurring operational problems in docs/problem-inventory.md, each with source link and "why automatable / why not". Build demo scenarios from the inventory.

## Local-only stack
- L1 No hosted inference, no API keys, Apple Silicon MacBook Pro only.
- L2 LM Studio OpenAI-compatible at localhost:1234/v1; LangChain ChatOpenAI at that base_url.
- L3 LangGraph for every agent: real StateGraph, typed state, conditional edges, checkpointing, interrupt_before on every human-approval node. No prompt chains dressed as agents.
- L4 LLM GGUF from Hugging Face, tool-calling capable; detect RAM at setup and recommend by tier (64GB+: Qwen3-30B-A3B-Instruct or Mistral-Small-3.2-24B; 32GB: Qwen3-14B; 16GB: Qwen3-8B or Qwen2.5-7B-Instruct); pin exact repo IDs and quant; verify tool-calling works before building on it; fallback constrained structured output, documented.
- L5 STT whisper.cpp large-v3-turbo or MLX Parakeet. TTS Kokoro-82M or Piper (USER OVERRIDE: use VibeVoice for TTS only, Australian accent). Diarisation pyannote community model or VAD+embeddings if licensing awkward; record in ADR.
- L6 All audio local; no cloud STT/TTS.
- L7 Single models.toml config; swapping models must not touch agent code.
- L8 Document measured tokens/sec, agent latency, transcription real-time factor on this machine. Real numbers.

## Integrity hard constraints
- I1 Never auto-denies, never blocks care; output is review flag + evidence routed to clinician.
- I2 Signals behavioural/account-level only: duplicate identity across accounts, reused payment instruments, questionnaire text matching known template/forum language, consult-shopping across clinicians in short window, implausible address or DOB churn, velocity anomalies.
- I3 Forbidden signals: postcode, ethnicity, name origin, age alone, gender, employment status, any proxy. A test that FAILS if a forbidden feature appears in the feature set.
- I4 Every flag carries evidence; no unexplainable scores.
- I5 Bias evaluation across synthetic cohorts reporting flag-rate disparity; report disparity, do not hide.
- I6 Name it "integrity signals" or "review triage" everywhere. Never "fraud", "drug seeker", "abuse".
- I7 docs/integrity-ethics.md: false positives cost a patient a delay, false negatives cost clinical safety, tuned deliberately toward the former.

## Regulatory hard constraints
- R1 No agent produces clinical or dosing advice, names prescription-only products to a patient, makes condition claims, or uses euphemisms for prescription-only treatments. Enforced at runtime in a dedicated guard node, not a system prompt. Adversarial tests.
- R2 Adverse events, suspected misuse, mental-health distress, pregnancy queries escalate immediately, never drafted.
- R3 Consult notes are clinician-review drafts; pipeline never finalises a record, never assigns a definitive diagnosis, never emits codes without confidence values and a human sign-off step.
- R4 Synthetic audio watermarked as synthetic in metadata; generator refuses to process any real audio file.
- R5 Rule sets in config keyed by jurisdiction (AU populated; UK and NZ stubbed with visible seam).
- R6 Synthetic data only, generated by SimClinic. PII redaction at ingress. No real patient data ever.
- R7 Cite statute/code sections neutrally. Do NOT reference any company's regulatory or enforcement history; do not name any specific clinic anywhere in the repo.

## Documentation
- D1 README (hiring manager, 4-minute read): what it is, 60-second demo path, one architecture diagram, measured results table, honest limitations. Integrity agent one-liner MUST lead with "flags for clinician review".
- D2 MkDocs Material built and published via GitHub Pages (USER RULING: from a local build pushed to gh-pages, no CI).
- D3 ADRs for every real choice: LangGraph vs alternatives, model selection, diarisation, where humans stay in the loop, checkpointing.
- D4 Mermaid diagrams of each LangGraph state machine generated FROM the graph definitions (cannot drift).
- D5 docs/problem-inventory.md, docs/integrity-ethics.md, docs/evaluation.md, docs/runbook.md ("what breaks and how you would know").
- D6 Full type hints, Google-style docstrings, mypy strict, ruff.
- D7 README HONESTY section: generated vs templated; measured vs assumed; what must change before production.

## Evaluation
- E1 Golden sets per agent. Report: intent accuracy, escalation recall (100% on clinical and adverse-event cases), rule-violation rate, draft acceptance rate, integrity flag precision/recall + cohort disparity, consult: WER, diarisation accuracy, note-field extraction F1, coding precision vs the generator's ground truth.
- E2 Pass/fail gate; regression blocks merge (USER RULING: no CI; the gate is a local `make ci` plus required commit statuses). Results table auto-generated into README.

## Process
- P1 Decompose into GitHub issues first, one-PR sized, explicit dependency edges where issues touch overlapping files; sequence those.
- P2 Strict TDD: failing test first. P3 Independent PR review; all reviewer types satisfied before merge. P4 Docs and changelog updated in every change. P5 Verify local == remote after each merge. P6 Do NOT auto-merge if any gate check fails, even with approvals; ask user.
- P7 Orchestrator (Sonnet) delegates parallelisable work to Haiku subagents with tight briefs; owns architecture, plan, all merges; subagents never merge. Roles: scaffolder, simwright, toolsmith, audiowright, evalsmith, scribe, reviewer. Own brief, own files, own tests; overlapping briefs sequenced, never parallel-then-rebase.
- P8 FIRST ACTION: read ad + site, produce problem inventory and full plan with open questions. Do not scaffold anything until user approves.

## Deliverables / scope
- X1 Repo with green CI + published docs. X2 One-page write-up mapping each job-ad requirement to evidence. X3 3-minute demo video script (order: consult audio playing -> structured note + codes with low-confidence flag -> Factory told a process out loud -> tests red to green -> triage refuses dosing question citing rule -> integrity flags duplicate identity for clinician review -> SimClinic with agent off, queue goes red).
- X4 Depth over breadth; if something gives, cut features, never tests, evals, docs.
