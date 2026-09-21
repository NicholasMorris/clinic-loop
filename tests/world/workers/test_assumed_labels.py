"""Tests for staffing configuration and assumed labels."""

import inspect
from pathlib import Path

import pytest

from clinicloop.world.workers import load_staffing
from clinicloop.world.workers.staffing import StaffingParameterMissing


def test_staffing_config_is_labelled_assumed_and_required(tmp_path: Path) -> None:
    """Verify staffing configuration requirements and constraints.

    Tests:
    1. Every pool in staffing.toml has assumed=true and non-empty assumption_note
    2. Every pool has required keys: service_time_family, staffing_level, hourly_cost,
       mean_service_minutes
    3. Missing required parameter raises StaffingParameterMissing with pool and key
    4. load_staffing signature has no default values for staffing, cost, or distribution
    """
    # Load the default staffing configuration
    default_config = load_staffing()

    # Check that all pools are marked as assumed
    for pool_name, config in default_config.items():
        assert config.assumed is True, f"Pool '{pool_name}' should have assumed=true"
        assert config.assumption_note and len(config.assumption_note) > 0, (
            f"Pool '{pool_name}' should have non-empty assumption_note"
        )
        assert config.service_time_family, f"Pool '{pool_name}' should have service_time_family"
        assert config.staffing_level > 0, f"Pool '{pool_name}' should have staffing_level > 0"
        assert config.hourly_cost > 0, f"Pool '{pool_name}' should have hourly_cost > 0"
        assert config.mean_service_minutes > 0, (
            f"Pool '{pool_name}' should have mean_service_minutes > 0"
        )

    # Verify specific mean service minute values from issue spec
    assert default_config["intake"].mean_service_minutes == 2
    assert default_config["prescriber_review"].mean_service_minutes == 8
    assert default_config["pharmacy_fulfilment"].mean_service_minutes == 4
    assert default_config["support_inbox"].mean_service_minutes == 14

    # Create a modified config file with mean_service_minutes removed from intake pool
    modified_toml_content = """\
[intake]
assumed = true
assumption_note = "Test"
service_time_family = "exponential"
staffing_level = 2
hourly_cost = 28.0

[prescriber_review]
assumed = true
assumption_note = "Test"
service_time_family = "normal"
staffing_level = 3
hourly_cost = 85.0
mean_service_minutes = 8

[pharmacy_fulfilment]
assumed = true
assumption_note = "Test"
service_time_family = "exponential"
staffing_level = 2
hourly_cost = 32.0
mean_service_minutes = 4

[support_inbox]
assumed = true
assumption_note = "Test"
service_time_family = "exponential"
staffing_level = 2
hourly_cost = 30.0
mean_service_minutes = 5
"""

    modified_config_path = tmp_path / "staffing_incomplete.toml"
    modified_config_path.write_text(modified_toml_content)

    # Loading with missing parameter should raise StaffingParameterMissing
    with pytest.raises(StaffingParameterMissing) as exc_info:
        load_staffing(modified_config_path)

    # Check the exception contains the correct pool and key
    assert exc_info.value.pool_name == "intake"
    assert exc_info.value.key == "mean_service_minutes"

    # Check that load_staffing has no default parameters
    sig = inspect.signature(load_staffing)
    for param_name, param in sig.parameters.items():
        # Only config_path can have a default (None)
        if param_name == "config_path":
            continue
        assert param.default == inspect.Parameter.empty, (
            f"Parameter '{param_name}' should not have a default value"
        )
