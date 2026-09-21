"""Templated message corpus builder."""

from typing import Any


def build_corpus(
    seed: int,
    count: int = 400,
) -> list[dict[str, Any]]:
    """Build a templated message corpus for the triage golden set.

    Args:
        seed: Random seed for reproducibility.
        count: Number of messages to generate (default 400).

    Returns:
        A list of message dictionaries with fields: message_id, patient_id,
        channel, body, intent, must_escalate, generation_method, template_id.
    """
    raise NotImplementedError("build_corpus not yet implemented")
