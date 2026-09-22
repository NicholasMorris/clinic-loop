# Cassettes

- `recorded_intent.jsonl` holds REAL responses recorded from the live local model by
  `scripts/record_triage_cassettes.py` (temperature 0, seed from the models.toml row). Each line
  carries the model id, the prompt hash, a UTC timestamp and the measured latency. It is keyed by
  the hash of the frozen prompt in `src/clinicloop/agents/triage/prompts.py`; editing that prompt
  requires re-recording. Nothing else may write this file.
- `synthetic_tool_binding.jsonl` (added with the tool-binding test) is a SYNTHETIC adversarial
  cassette, written by hand to model a compromised answer that names identifiers. It is not a
  recording.
