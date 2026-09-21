"""Parse and validate the LLM model selection ADR."""

from typing import Any, TypedDict


class ModelRole(TypedDict):
    """Model selection for a given role.

    Attributes:
        model_id: The model identifier.
        pass_count: Number of cases passed out of 30.
        tokens_per_second: Measured generation speed.
        family: The model family (e.g., 'qwen', 'gpt_oss', 'gemma').
    """

    model_id: str
    pass_count: int
    tokens_per_second: float
    family: str


class ModelSelectionADR(TypedDict):
    """Parsed model selection ADR.

    Attributes:
        status: The ADR status (e.g., 'Accepted').
        roles: Dict of role name to ModelRole (primary, judge, fallback).
    """

    status: str
    roles: dict[str, ModelRole]


def parse_model_selection_adr(adr_path: str) -> ModelSelectionADR:
    """Parse the LLM model selection ADR.

    Reads and validates docs/adr/llm-model-selection.md. The ADR must:
    - Have status 'Accepted'
    - Name exactly the roles: primary, judge, fallback
    - Each role carries: pass count, tokens-per-second, family
    - Judge family must differ from primary family
    - Primary pass count >= promotion_bar().primary_min_passing_cases

    Args:
        adr_path: Path to the ADR file (typically docs/adr/llm-model-selection.md).

    Returns:
        A ModelSelectionADR dict with status and roles.

    Raises:
        NotImplementedError: Stub implementation.
    """
    raise NotImplementedError("parse_model_selection_adr stub")
