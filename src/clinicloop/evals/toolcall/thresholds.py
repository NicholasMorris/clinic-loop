"""Model promotion bar thresholds loaded from config."""

import tomllib
from pathlib import Path

from pydantic import BaseModel, Field


class PromotionBar(BaseModel):
    """Configuration for model promotion thresholds.

    Attributes:
        primary_min_passing_cases: Minimum passing cases required for primary model (out of 30).
        fallback_min_passing_cases: Minimum passing cases required for fallback model (out of 30).
        max_schema_invalid_outputs: Maximum allowed schema-invalid outputs (0 means none).
    """

    primary_min_passing_cases: int = Field(description="Minimum passing cases for primary model")
    fallback_min_passing_cases: int = Field(description="Minimum passing cases for fallback model")
    max_schema_invalid_outputs: int = Field(description="Maximum schema-invalid outputs allowed")


def promotion_bar() -> PromotionBar:
    """Read promotion bar thresholds from evals/toolcall/thresholds.toml.

    The config file must contain all three keys; no defaults are provided in code.

    Returns:
        A PromotionBar with primary_min_passing_cases, fallback_min_passing_cases,
        and max_schema_invalid_outputs loaded from config.

    Raises:
        FileNotFoundError: If the config file is not found.
        ValueError: If required keys are missing from the config.
    """
    # Path from src/clinicloop/evals/toolcall/thresholds.py to repo root: go up 5 levels
    config_path = (
        Path(__file__).parent.parent.parent.parent.parent / "evals" / "toolcall" / "thresholds.toml"
    )

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "rb") as f:
        data = tomllib.load(f)

    # Validate that all required keys are present
    required_keys = {
        "primary_min_passing_cases",
        "fallback_min_passing_cases",
        "max_schema_invalid_outputs",
    }
    missing_keys = required_keys - set(data.keys())
    if missing_keys:
        raise ValueError(f"Missing required keys in config: {missing_keys}")

    return PromotionBar(
        primary_min_passing_cases=data["primary_min_passing_cases"],
        fallback_min_passing_cases=data["fallback_min_passing_cases"],
        max_schema_invalid_outputs=data["max_schema_invalid_outputs"],
    )
