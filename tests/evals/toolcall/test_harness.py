"""Tests AC3 and AC4: Harness scoring on scripted models."""

from clinicloop.evals.toolcall.harness import score_case


def test_prose_response_scores_as_failed_case() -> None:
    """AC3: A prose response produces emitted_tool_call=False, tool_name_matches=False.

    The harness counts such cases in failed_cases rather than raising.
    """
    # When a model returns prose instead of a tool call,
    # score_case should return a dict with emitted_tool_call=False
    result = score_case(
        case_id="test_001",
        model_response="This is just prose, not a tool call.",
        expected_tool_name="get_weather",
        expected_schema={"type": "object", "properties": {"location": {"type": "string"}}},
    )

    assert result["emitted_tool_call"] is False


def test_wrong_argument_type_scores_arguments_invalid() -> None:
    """AC4: Calling the right tool with wrong argument types.

    Produces tool_name_matches=True but arguments_valid=False.
    """
    # When a model calls the expected tool but with wrong argument types
    result = score_case(
        case_id="test_002",
        model_response="""{
            "type": "tool_call",
            "tool_name": "get_weather",
            "arguments": {"location": 42}
        }""",
        expected_tool_name="get_weather",
        expected_schema={
            "type": "object",
            "properties": {"location": {"type": "string"}},
            "required": ["location"],
        },
    )

    assert result["tool_name_matches"] is True
    assert result["arguments_valid"] is False
