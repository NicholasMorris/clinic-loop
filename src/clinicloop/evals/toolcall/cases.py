"""Tool-call test case set: exactly 30 cases with deterministic ordering."""

from typing import Any, TypedDict


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
    tool_schema: dict[str, Any]
    prompt: str


def load_cases() -> list[ToolCallCase]:
    """Load the set of 30 tool-call test cases in deterministic order.

    Returns:
        A list of exactly 30 ToolCallCase dicts, with stable ordering across calls.

    Raises:
        NotImplementedError: Stub implementation.
    """
    cases: list[ToolCallCase] = [
        {
            "case_id": "tool_call_001",
            "tool_name": "get_weather",
            "tool_schema": {
                "type": "object",
                "properties": {"location": {"type": "string"}},
                "required": ["location"],
            },
            "prompt": "What is the weather in San Francisco?",
        },
        {
            "case_id": "tool_call_002",
            "tool_name": "search_documents",
            "tool_schema": {
                "type": "object",
                "properties": {"query": {"type": "string"}, "limit": {"type": "integer"}},
                "required": ["query"],
            },
            "prompt": "Search for documents about climate change.",
        },
        {
            "case_id": "tool_call_003",
            "tool_name": "create_event",
            "tool_schema": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "date": {"type": "string"},
                    "time": {"type": "string"},
                },
                "required": ["title", "date"],
            },
            "prompt": "Create a meeting called 'Team Sync' on 2025-01-15.",
        },
        {
            "case_id": "tool_call_004",
            "tool_name": "calculate_sum",
            "tool_schema": {
                "type": "object",
                "properties": {"numbers": {"type": "array", "items": {"type": "number"}}},
                "required": ["numbers"],
            },
            "prompt": "Add up 10, 20, and 30.",
        },
        {
            "case_id": "tool_call_005",
            "tool_name": "get_user_info",
            "tool_schema": {
                "type": "object",
                "properties": {"user_id": {"type": "string"}},
                "required": ["user_id"],
            },
            "prompt": "Get information about user ID 12345.",
        },
        {
            "case_id": "tool_call_006",
            "tool_name": "send_email",
            "tool_schema": {
                "type": "object",
                "properties": {
                    "to": {"type": "string"},
                    "subject": {"type": "string"},
                    "body": {"type": "string"},
                },
                "required": ["to", "subject", "body"],
            },
            "prompt": "Send email to alice@example.com with subject 'Hello' and body 'Hi'.",
        },
        {
            "case_id": "tool_call_007",
            "tool_name": "list_files",
            "tool_schema": {
                "type": "object",
                "properties": {"directory": {"type": "string"}},
                "required": ["directory"],
            },
            "prompt": "List files in the /home/user/documents directory.",
        },
        {
            "case_id": "tool_call_008",
            "tool_name": "database_query",
            "tool_schema": {
                "type": "object",
                "properties": {"sql": {"type": "string"}},
                "required": ["sql"],
            },
            "prompt": "Query all rows from the users table where age > 18.",
        },
        {
            "case_id": "tool_call_009",
            "tool_name": "translate_text",
            "tool_schema": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "target_language": {"type": "string"},
                },
                "required": ["text", "target_language"],
            },
            "prompt": "Translate 'Hello, world!' to Spanish.",
        },
        {
            "case_id": "tool_call_010",
            "tool_name": "get_stock_price",
            "tool_schema": {
                "type": "object",
                "properties": {"symbol": {"type": "string"}},
                "required": ["symbol"],
            },
            "prompt": "What is the stock price for AAPL?",
        },
        {
            "case_id": "tool_call_011",
            "tool_name": "set_alarm",
            "tool_schema": {
                "type": "object",
                "properties": {
                    "time": {"type": "string"},
                    "label": {"type": "string"},
                },
                "required": ["time"],
            },
            "prompt": "Set an alarm for 6:30 AM called 'Morning'.",
        },
        {
            "case_id": "tool_call_012",
            "tool_name": "resize_image",
            "tool_schema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "width": {"type": "integer"},
                    "height": {"type": "integer"},
                },
                "required": ["path", "width", "height"],
            },
            "prompt": "Resize image.jpg to 800x600 pixels.",
        },
        {
            "case_id": "tool_call_013",
            "tool_name": "fetch_url",
            "tool_schema": {
                "type": "object",
                "properties": {"url": {"type": "string"}},
                "required": ["url"],
            },
            "prompt": "Fetch the contents of https://example.com.",
        },
        {
            "case_id": "tool_call_014",
            "tool_name": "delete_file",
            "tool_schema": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            },
            "prompt": "Delete the file /tmp/temp.txt.",
        },
        {
            "case_id": "tool_call_015",
            "tool_name": "count_words",
            "tool_schema": {
                "type": "object",
                "properties": {"text": {"type": "string"}},
                "required": ["text"],
            },
            "prompt": "How many words are in 'The quick brown fox jumps over the lazy dog'?",
        },
        {
            "case_id": "tool_call_016",
            "tool_name": "convert_currency",
            "tool_schema": {
                "type": "object",
                "properties": {
                    "amount": {"type": "number"},
                    "from_currency": {"type": "string"},
                    "to_currency": {"type": "string"},
                },
                "required": ["amount", "from_currency", "to_currency"],
            },
            "prompt": "Convert 100 USD to EUR.",
        },
        {
            "case_id": "tool_call_017",
            "tool_name": "schedule_backup",
            "tool_schema": {
                "type": "object",
                "properties": {
                    "time": {"type": "string"},
                    "frequency": {"type": "string"},
                },
                "required": ["time"],
            },
            "prompt": "Schedule a backup at 2 AM daily.",
        },
        {
            "case_id": "tool_call_018",
            "tool_name": "analyze_sentiment",
            "tool_schema": {
                "type": "object",
                "properties": {"text": {"type": "string"}},
                "required": ["text"],
            },
            "prompt": "What is the sentiment of 'I love this product!'?",
        },
        {
            "case_id": "tool_call_019",
            "tool_name": "get_recommendations",
            "tool_schema": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string"},
                    "count": {"type": "integer"},
                },
                "required": ["user_id"],
            },
            "prompt": "Get 5 recommendations for user 999.",
        },
        {
            "case_id": "tool_call_020",
            "tool_name": "validate_email",
            "tool_schema": {
                "type": "object",
                "properties": {"email": {"type": "string"}},
                "required": ["email"],
            },
            "prompt": "Is test@example.com a valid email?",
        },
        {
            "case_id": "tool_call_021",
            "tool_name": "parse_json",
            "tool_schema": {
                "type": "object",
                "properties": {"json_string": {"type": "string"}},
                "required": ["json_string"],
            },
            "prompt": 'Parse this JSON: {"key": "value"}.',
        },
        {
            "case_id": "tool_call_022",
            "tool_name": "compress_file",
            "tool_schema": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            },
            "prompt": "Compress the file document.pdf.",
        },
        {
            "case_id": "tool_call_023",
            "tool_name": "find_duplicates",
            "tool_schema": {
                "type": "object",
                "properties": {
                    "items": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["items"],
            },
            "prompt": "Find duplicates in: apple, banana, apple, cherry.",
        },
        {
            "case_id": "tool_call_024",
            "tool_name": "generate_password",
            "tool_schema": {
                "type": "object",
                "properties": {"length": {"type": "integer"}},
                "required": ["length"],
            },
            "prompt": "Generate a 16-character password.",
        },
        {
            "case_id": "tool_call_025",
            "tool_name": "calculate_hash",
            "tool_schema": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "algorithm": {"type": "string"},
                },
                "required": ["text"],
            },
            "prompt": "Calculate the SHA-256 hash of 'hello'.",
        },
        {
            "case_id": "tool_call_026",
            "tool_name": "check_syntax",
            "tool_schema": {
                "type": "object",
                "properties": {
                    "code": {"type": "string"},
                    "language": {"type": "string"},
                },
                "required": ["code", "language"],
            },
            "prompt": "Check if this Python code is valid: print('hello')",
        },
        {
            "case_id": "tool_call_027",
            "tool_name": "merge_arrays",
            "tool_schema": {
                "type": "object",
                "properties": {
                    "array1": {"type": "array", "items": {"type": "string"}},
                    "array2": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["array1", "array2"],
            },
            "prompt": "Merge [a, b] and [c, d].",
        },
        {
            "case_id": "tool_call_028",
            "tool_name": "format_date",
            "tool_schema": {
                "type": "object",
                "properties": {
                    "date": {"type": "string"},
                    "format": {"type": "string"},
                },
                "required": ["date", "format"],
            },
            "prompt": "Format 2025-01-15 as MM/DD/YYYY.",
        },
        {
            "case_id": "tool_call_029",
            "tool_name": "get_random_number",
            "tool_schema": {
                "type": "object",
                "properties": {
                    "min": {"type": "integer"},
                    "max": {"type": "integer"},
                },
                "required": ["min", "max"],
            },
            "prompt": "Get a random number between 1 and 100.",
        },
        {
            "case_id": "tool_call_030",
            "tool_name": "summarize_text",
            "tool_schema": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "max_length": {"type": "integer"},
                },
                "required": ["text"],
            },
            "prompt": "Summarize this long document in 100 words.",
        },
    ]
    return cases
