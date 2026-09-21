"""Tool-call harness: run cases against a model and score results."""

import json
from typing import Any

from clinicloop.evals.toolcall.records import ToolCallResult


def _validate_against_schema(data: Any, schema: dict[str, Any]) -> bool:
    """Validate data against a JSON schema (simplified validation).

    Args:
        data: The data to validate.
        schema: The JSON schema.

    Returns:
        True if data matches schema, False otherwise.
    """
    schema_type = schema.get("type")

    if schema_type == "object":
        if not isinstance(data, dict):
            return False
        properties = schema.get("properties", {})
        required = schema.get("required", [])

        # Check required fields
        for req_field in required:
            if req_field not in data:
                return False

        # Check property types
        for field, value in data.items():
            if field in properties:
                field_schema = properties[field]
                field_type = field_schema.get("type")
                if field_type == "string" and not isinstance(value, str):
                    return False
                if field_type == "integer" and not isinstance(value, int):
                    return False
                if field_type == "number" and not isinstance(value, (int, float)):
                    return False
                if field_type == "array" and not isinstance(value, list):
                    return False
                if field_type == "boolean" and not isinstance(value, bool):
                    return False

        return True

    if schema_type == "string":
        return isinstance(data, str)
    if schema_type == "integer":
        return isinstance(data, int)
    if schema_type == "number":
        return isinstance(data, (int, float))
    if schema_type == "array":
        return isinstance(data, list)
    if schema_type == "boolean":
        return isinstance(data, bool)

    return True


def score_case(
    case_id: str,
    model_response: str,
    expected_tool_name: str,
    expected_schema: dict[str, Any],
) -> dict[str, Any]:
    """Score a single case response.

    Evaluates whether the model response:
    - Contains a syntactically valid tool call
    - Calls the expected tool
    - Provides arguments matching the expected schema

    Args:
        case_id: The case identifier.
        model_response: The raw response from the model.
        expected_tool_name: The tool name the model should call.
        expected_schema: JSON schema for expected arguments.

    Returns:
        A dict with keys: emitted_tool_call, tool_name_matches, arguments_valid.
    """
    emitted_tool_call = False
    tool_name_matches = False
    arguments_valid = False

    # Try to parse JSON from the response
    try:
        # Try to find a JSON object in the response
        json_start = model_response.find("{")
        if json_start == -1:
            return {
                "emitted_tool_call": False,
                "tool_name_matches": False,
                "arguments_valid": False,
            }

        json_end = model_response.rfind("}") + 1
        json_str = model_response[json_start:json_end]
        parsed = json.loads(json_str)

        # Check if it looks like a tool call
        if not isinstance(parsed, dict):
            return {
                "emitted_tool_call": False,
                "tool_name_matches": False,
                "arguments_valid": False,
            }

        # Check for tool_name field
        tool_name = parsed.get("tool_name") or parsed.get("name")
        if not tool_name:
            return {
                "emitted_tool_call": False,
                "tool_name_matches": False,
                "arguments_valid": False,
            }

        emitted_tool_call = True

        # Check if tool name matches
        if tool_name == expected_tool_name:
            tool_name_matches = True

            # Check if arguments are valid
            arguments = parsed.get("arguments", {})
            if _validate_against_schema(arguments, expected_schema):
                arguments_valid = True

    except (json.JSONDecodeError, ValueError, TypeError):
        pass

    return {
        "emitted_tool_call": emitted_tool_call,
        "tool_name_matches": tool_name_matches,
        "arguments_valid": arguments_valid,
    }


def run_harness(
    model_id: str,
    cases: list[dict[str, Any]],
) -> tuple[list[ToolCallResult], dict[str, Any]]:
    """Run the harness against all 30 cases for a given model.

    Args:
        model_id: The model identifier.
        cases: List of test cases from load_cases().

    Returns:
        A tuple of (per_case_results, run_summary).
        run_summary has keys: passed_cases, failed_cases.

    Raises:
        NotImplementedError: Stub implementation requires actual model integration.
    """
    # This is a stub that would need actual model integration.
    # For now, we'll return empty results.
    raise NotImplementedError("run_harness requires model integration stub")
