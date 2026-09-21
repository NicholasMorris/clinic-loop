"""Model promotion bar thresholds loaded from config."""

from pydantic import BaseModel, Field


class PromotionBar(BaseModel):
    """Configuration for model promotion thresholds.

    Attributes:
        primary_min_passing_cases: Minimum passing cases required for primary model (out of 30).
        fallback_min_passing_cases: Minimum passing cases required for fallback model (out of 30).
        max_schema_invalid_outputs: Maximum allowed schema-invalid outputs (0 means none).
    """

    primary_min_passing_cases: int = Field(
        description="Minimum passing cases for primary model"
    )
    fallback_min_passing_cases: int = Field(
        description="Minimum passing cases for fallback model"
    )
    max_schema_invalid_outputs: int = Field(description="Maximum schema-invalid outputs allowed")


def promotion_bar() -> PromotionBar:
    """Read promotion bar thresholds from evals/toolcall/thresholds.toml.

    The config file must contain all three keys; no defaults are provided in code.

    Returns:
        A PromotionBar with primary_min_passing_cases, fallback_min_passing_cases,
        and max_schema_invalid_outputs loaded from config.

    Raises:
        NotImplementedError: Stub implementation.
    """
    raise NotImplementedError("promotion_bar stub")
