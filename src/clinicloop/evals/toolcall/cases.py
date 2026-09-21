"""Tool-call test case set: exactly 30 cases with deterministic ordering."""

from typing import TypedDict


class ToolCallCase(TypedDict):
    """Schema for a single tool-call test case.

    Attributes:
        case_id: Unique identifier for this case.
        tool_name: The expected tool name.
        tool_schema: JSON schema for the expected tool arguments.
        prompt: The LLM prompt for this case.
    """

    case_id: str
    tool_name: str
    tool_schema: dict
    prompt: str


def load_cases() -> list[ToolCallCase]:
    """Load the set of 30 tool-call test cases in deterministic order.

    Returns:
        A list of exactly 30 ToolCallCase dicts, with stable ordering across calls.

    Raises:
        NotImplementedError: Stub implementation.
    """
    raise NotImplementedError("load_cases stub")
