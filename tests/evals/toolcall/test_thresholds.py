"""Test AC6: Promotion bar reads from config with no code default."""

from pathlib import Path
import tempfile
import pytest
from pydantic import ValidationError

from clinicloop.evals.toolcall.thresholds import promotion_bar, PromotionBar


def test_promotion_bar_read_from_config_with_no_code_default() -> None:
    """AC6: promotion_bar() reads thresholds from evals/toolcall/thresholds.toml.

    No code defaults are provided; every key is required in the config.
    """
    # Call promotion_bar() - this will load from the actual config file
    bar = promotion_bar()

    # Must have all three required fields with exact expected values
    assert bar.primary_min_passing_cases == 27
    assert bar.fallback_min_passing_cases == 24
    assert bar.max_schema_invalid_outputs == 0

    # Verify the type
    assert isinstance(bar, PromotionBar)


def test_promotion_bar_requires_all_config_keys() -> None:
    """Verify that promotion_bar requires all keys in the config file.

    If a required key is missing from the TOML, ValidationError is raised.
    """
    # This test verifies the schema by attempting to construct PromotionBar
    # without each required key

    required_keys = [
        "primary_min_passing_cases",
        "fallback_min_passing_cases",
        "max_schema_invalid_outputs",
    ]

    for missing_key in required_keys:
        data = {
            "primary_min_passing_cases": 27,
            "fallback_min_passing_cases": 24,
            "max_schema_invalid_outputs": 0,
        }
        del data[missing_key]

        with pytest.raises(ValidationError):
            PromotionBar(**data)
