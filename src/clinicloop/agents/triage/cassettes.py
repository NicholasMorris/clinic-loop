"""File-backed cassettes of real model responses.

A cassette line is JSON: model_id, prompt_hash, sample_index, seed, response, recorded_at,
latency_s. Replay looks a response up by (model_id, prompt_hash, sample_index, seed) and never
falls back to a live call.
"""

import hashlib
import json
from pathlib import Path
from typing import Any

from clinicloop.evals.core.cassettes import cassette_key

CassetteKey = tuple[str, str, int, int]


class CassetteMiss(KeyError):
    """Raised when replay finds no recorded response for a key."""


def prompt_hash(prompt: str) -> str:
    """SHA-256 hex digest of the exact prompt text."""
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()


def load_cassette_file(path: Path) -> dict[CassetteKey, str]:
    """Load every recorded response from a JSONL cassette file."""
    entries: dict[CassetteKey, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        key = cassette_key(rec["model_id"], rec["prompt_hash"], rec["sample_index"], rec["seed"])
        entries[key] = rec["response"]
    return entries


def append_record(path: Path, record: dict[str, Any]) -> None:
    """Append one recorded response to a JSONL cassette file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=True) + "\n")
