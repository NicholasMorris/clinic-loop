"""Model ports the triage nodes talk to: fake, cassette replay, recording and live adapters."""

import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

from clinicloop.evals.core.cassettes import cassette_key

from .cassettes import CassetteMiss, append_record, load_cassette_file, prompt_hash


class ModelPort(Protocol):
    """The one call the nodes make: prompt in, text out."""

    def complete(self, prompt: str, *, sample_index: int = 0) -> str:
        """Return the model's text for a prompt."""
        ...


class FakeModelPort:
    """Replays scripted responses in order and records every prompt it was given."""

    def __init__(self, responses: list[str]) -> None:
        """Create a fake with the scripted responses."""
        self._responses = list(responses)
        self.prompts: list[str] = []

    def complete(self, prompt: str, *, sample_index: int = 0) -> str:
        """Return the next scripted response."""
        self.prompts.append(prompt)
        if not self._responses:
            raise IndexError("FakeModelPort has no scripted responses left")
        return self._responses.pop(0)


class CassetteModelPort:
    """Replays recorded responses; a missing key raises CassetteMiss, never a live call."""

    def __init__(self, model_id: str, seed: int, cassette_paths: list[Path]) -> None:
        """Load every cassette file for one model id and seed."""
        self.model_id = model_id
        self.seed = seed
        self._entries: dict[tuple[str, str, int, int], str] = {}
        for path in cassette_paths:
            self._entries.update(load_cassette_file(path))

    def complete(self, prompt: str, *, sample_index: int = 0) -> str:
        """Return the recorded response for this prompt."""
        key = cassette_key(self.model_id, prompt_hash(prompt), sample_index, self.seed)
        if key not in self._entries:
            raise CassetteMiss(f"no cassette for model={self.model_id} prompt_hash={key[1][:12]}")
        return self._entries[key]


class ChatModelPort:
    """Adapts a LangChain chat model (built by clinicloop.llm) to ModelPort."""

    def __init__(self, chat_model: Any) -> None:
        """Wrap a chat model with an `invoke(str)` method."""
        self._chat_model = chat_model

    def complete(self, prompt: str, *, sample_index: int = 0) -> str:
        """Call the chat model and return its text."""
        return str(self._chat_model.invoke(prompt).content)


class RecordingModelPort:
    """Calls a live chat model and appends each real response to a cassette file."""

    def __init__(self, chat_model: Any, model_id: str, seed: int, path: Path) -> None:
        """Record responses from `chat_model` into the JSONL file at `path`."""
        self._chat_model = chat_model
        self.model_id = model_id
        self.seed = seed
        self.path = path

    def complete(self, prompt: str, *, sample_index: int = 0) -> str:
        """Call the live model, record the response, and return it."""
        started = time.monotonic()
        response = str(self._chat_model.invoke(prompt).content)
        append_record(
            self.path,
            {
                "model_id": self.model_id,
                "prompt_hash": prompt_hash(prompt),
                "sample_index": sample_index,
                "seed": self.seed,
                "response": response,
                "recorded_at": datetime.now(timezone.utc).isoformat(),
                "latency_s": round(time.monotonic() - started, 3),
            },
        )
        return response
