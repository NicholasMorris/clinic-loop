"""Tool-call harness: run cases against a model and score results."""

import json
import time
import urllib.request
from collections.abc import Sequence
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
    cases: Sequence[Any],
    base_url: str = "http://localhost:1234/v1",
    max_tokens: int = 500,
) -> tuple[list[ToolCallResult], dict[str, Any]]:
    """Run the harness against all 30 cases for a given model.

    Sends each case prompt to the model with tool specifications, records
    whether a valid tool call was emitted, tool name matches, and arguments
    are valid. Measures latency and tokens per second for each case.

    Args:
        model_id: The model identifier.
        cases: List of test cases from load_cases().
        base_url: Base URL for the LM Studio API.
        max_tokens: Maximum tokens to generate per case.

    Returns:
        A tuple of (per_case_results, run_summary).
        per_case_results: List of ToolCallResult records.
        run_summary: Dict with keys: passed_cases, failed_cases.

    Raises:
        RuntimeError: If model API calls fail.
    """
    per_case_results: list[ToolCallResult] = []
    url = f"{base_url}/chat/completions"

    passed_cases = 0
    failed_cases = 0

    for case in cases:
        case_id = case["case_id"]
        tool_name = case["tool_name"]
        tool_schema = case["tool_schema"]
        prompt = case["prompt"]

        # Build tool definition for this case
        tool_def = {
            "type": "function",
            "function": {
                "name": tool_name,
                "description": f"Tool for case {case_id}",
                "parameters": tool_schema,
            },
        }

        # Build request
        data = {
            "model": model_id,
            "messages": [{"role": "user", "content": prompt}],
            "tools": [tool_def],
            "tool_choice": "auto",
            "max_tokens": max_tokens,
        }

        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(data).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )

            start_time = time.time()
            with urllib.request.urlopen(req, timeout=120) as response:
                elapsed_sec = time.time() - start_time
                latency_ms = elapsed_sec * 1000

                result = json.loads(response.read())
                response_text = ""

                # Extract response and tool calls
                if result.get("choices"):
                    message = result["choices"][0].get("message", {})
                    response_text = message.get("content", "")
                    tool_calls = message.get("tool_calls", [])

                    # If there are tool calls, format them for scoring
                    if tool_calls:
                        # Use the first tool call
                        tool_call = tool_calls[0]
                        tool_call_obj = {
                            "tool_name": tool_call.get("function", {}).get("name", ""),
                            "arguments": json.loads(
                                tool_call.get("function", {}).get("arguments", "{}")
                            ),
                        }
                        response_text = json.dumps(tool_call_obj)

                # Score the case
                scoring = score_case(case_id, response_text, tool_name, tool_schema)

                # Calculate tokens per second
                completion_tokens = result.get("usage", {}).get("completion_tokens", 0)
                tokens_per_sec = completion_tokens / elapsed_sec if elapsed_sec > 0 else 0.0

                # Create result record
                result_record = ToolCallResult(
                    case_id=case_id,
                    model_id=model_id,
                    emitted_tool_call=scoring["emitted_tool_call"],
                    tool_name_matches=scoring["tool_name_matches"],
                    arguments_valid=scoring["arguments_valid"],
                    latency_ms=latency_ms,
                    tokens_per_second=tokens_per_sec,
                )

                per_case_results.append(result_record)

                # Count pass/fail
                if (
                    scoring["emitted_tool_call"]
                    and scoring["tool_name_matches"]
                    and scoring["arguments_valid"]
                ):
                    passed_cases += 1
                else:
                    failed_cases += 1

        except Exception:
            # On error, record a failed case
            result_record = ToolCallResult(
                case_id=case_id,
                model_id=model_id,
                emitted_tool_call=False,
                tool_name_matches=False,
                arguments_valid=False,
                latency_ms=0.0,
                tokens_per_second=0.0,
            )
            per_case_results.append(result_record)
            failed_cases += 1

    run_summary = {
        "passed_cases": passed_cases,
        "failed_cases": failed_cases,
        "total_cases": len(cases),
    }

    return per_case_results, run_summary
