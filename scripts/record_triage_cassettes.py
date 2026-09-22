#!/usr/bin/env python
"""Record REAL intent-classification responses from the live local model into a cassette file.

Run by the orchestrator against LM Studio (127.0.0.1:1234):
    uv run python scripts/record_triage_cassettes.py --role primary

The cassette file is the only source for the classify_intent replay tests; nothing else may
write it. Temperature is pinned to 0 and the seed comes from the models.toml row.
"""

import argparse
import json
from pathlib import Path

from clinicloop.agents.triage.models import RecordingModelPort
from clinicloop.agents.triage.prompts import build_classify_prompt, build_data_block
from clinicloop.llm import build_chat_model, load_models_config
from clinicloop.llm.config import get_models_config

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "agents" / "triage_nodes" / "fixtures" / "intent_threads.jsonl"
DEFAULT_OUT = ROOT / "tests" / "agents" / "triage_nodes" / "cassettes" / "recorded_intent.jsonl"


def main() -> None:
    """Record one response per fixture message."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--role", default="primary", help="models.toml row to record from")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    load_models_config(ROOT / "models.toml")
    row = getattr(get_models_config(), args.role)
    chat_model = build_chat_model(args.role).bind(temperature=0, seed=row.seed)
    if args.out.exists():
        args.out.unlink()
    port = RecordingModelPort(chat_model, row.repo_id or args.role, row.seed, args.out)
    for line in FIXTURE.read_text().splitlines():
        case = json.loads(line)
        prompt = build_classify_prompt(build_data_block(case["text"]))
        answer = port.complete(prompt)
        print(f"{case['id']} {case['label']:24} -> {answer.strip()[:60]}")


if __name__ == "__main__":
    main()
