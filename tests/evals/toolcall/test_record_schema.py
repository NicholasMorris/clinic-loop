"""Test AC2: Result record schema validation."""

import pytest
from pydantic import ValidationError

from clinicloop.evals.toolcall.records import ToolCallResult


def test_result_record_requires_all_fields() -> None:
    """AC2: Each result record must carry all required fields.

    ValidationError is raised naming any missing field.
    """
    # Valid record with all fields
    valid_record = ToolCallResult(
        case_id="case_001",
        model_id="primary",
        emitted_tool_call=True,
        tool_name_matches=True,
        arguments_valid=True,
        latency_ms=123.4,
        tokens_per_second=45.6,
    )

    assert valid_record.case_id == "case_001"

    # Test each field is required by trying to construct without it
    required_fields = [
        "case_id",
        "model_id",
        "emitted_tool_call",
        "tool_name_matches",
        "arguments_valid",
        "latency_ms",
        "tokens_per_second",
    ]

    for field in required_fields:
        data: dict[str, str | bool | float] = {
            "case_id": "case_001",
            "model_id": "primary",
            "emitted_tool_call": True,
            "tool_name_matches": True,
            "arguments_valid": True,
            "latency_ms": 123.4,
            "tokens_per_second": 45.6,
        }
        del data[field]

        with pytest.raises(ValidationError) as exc_info:
            ToolCallResult(**data)  # type: ignore

        # The error message should name the missing field
        assert field in str(exc_info.value), (
            f"Missing field {field} should be named in ValidationError: {exc_info.value}"
        )
