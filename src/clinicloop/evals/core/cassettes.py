"""Cassette key and lookup for recorded LLM responses."""

from typing import Any


def cassette_key(
    model_id: str, prompt_hash: str, sample_index: int, seed: int
) -> tuple[str, str, int, int]:
    """Generate a cassette key for a recorded LLM response.

    The key consists of the model id, prompt hash, sample index, and seed.
    Two lookups differing only in sample index will return different recorded
    responses.

    Args:
        model_id: The model identifier.
        prompt_hash: The SHA256 hash of the prompt.
        sample_index: The sample index (0, 1, 2, ...).
        seed: The random seed.

    Returns:
        A tuple (model_id, prompt_hash, sample_index, seed).
    """
    raise NotImplementedError


def lookup(key: tuple[str, str, int, int]) -> Any:
    """Look up a recorded LLM response by cassette key.

    Args:
        key: The cassette key tuple.

    Returns:
        The recorded response.
    """
    raise NotImplementedError
