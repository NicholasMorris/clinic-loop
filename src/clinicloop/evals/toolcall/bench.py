"""Benchmark utilities: measure tokens per second."""

from typing import Any


def measure_tokens_per_second(
    model_id: str,
    prompt: str,
) -> float:
    """Measure tokens per second for a model on a given prompt.

    Args:
        model_id: The model identifier.
        prompt: The prompt to measure.

    Returns:
        Tokens per second (completion tokens / wall time in seconds).

    Raises:
        NotImplementedError: Stub implementation.
    """
    raise NotImplementedError("measure_tokens_per_second stub")
