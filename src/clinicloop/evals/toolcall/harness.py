"""Tool-call harness: run cases against a model and score results."""

from typing import Any

from clinicloop.evals.toolcall.records import ToolCallResult


def score_case(
    case_id: str,
    model_response: str,
    expected_tool_name: str,
    expected_schema: dict,
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

    Raises:
        NotImplementedError: Stub implementation.
    """
    raise NotImplementedError("score_case stub")


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
        run_summary has keys: passed_cases, failed_cases, schema_invalid_outputs.

    Raises:
        NotImplementedError: Stub implementation.
    """
    raise NotImplementedError("run_harness stub")
