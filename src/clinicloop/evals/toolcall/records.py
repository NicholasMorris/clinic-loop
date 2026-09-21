"""Per-case result record schema for tool-call evaluation."""

from pydantic import BaseModel, Field


class ToolCallResult(BaseModel):
    """Schema for a single tool-call evaluation case result.

    Attributes:
        case_id: Unique identifier for the test case.
        model_id: The model identifier that was tested.
        emitted_tool_call: Whether the model emitted a syntactically valid tool call.
        tool_name_matches: Whether the tool name matches the expected tool.
        arguments_valid: Whether the arguments match the expected schema.
        latency_ms: Time taken to generate the tool call in milliseconds.
        tokens_per_second: Generation speed in tokens per second.
    """

    case_id: str = Field(description="Unique identifier for the test case")
    model_id: str = Field(description="The model identifier that was tested")
    emitted_tool_call: bool = Field(description="Whether a valid tool call was emitted")
    tool_name_matches: bool = Field(description="Whether the tool name matches expected")
    arguments_valid: bool = Field(description="Whether arguments match expected schema")
    latency_ms: float = Field(description="Latency in milliseconds")
    tokens_per_second: float = Field(description="Generation speed in tokens per second")
