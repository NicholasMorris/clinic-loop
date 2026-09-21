"""Tests for structured output methods."""

import tempfile
from pathlib import Path
from typing import Any, cast
from unittest.mock import MagicMock, patch

from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from clinicloop.llm.config import load_models_config
from clinicloop.llm.factory import build_chat_model
from clinicloop.llm.structured import structured_output


class SimpleSchema(BaseModel):
    """Simple test schema."""

    name: str
    value: int


def test_json_schema_path_sends_no_tools_key() -> None:
    """AC4: JSON schema path sends no tools key and sets structured_method_used."""
    toml_content = """
[primary]
kind = "server"
repo_id = "unsloth/Qwen3-30B-A3B-Instruct-2507-GGUF"
revision = "abc1234567890def"
quant = "Q4_K_M"
family = "qwen"
base_url = "http://127.0.0.1:1234/v1"
structured_method = "json_schema"
parallel_tool_calls = false
reasoning_handling = "disabled"
context_window = 8000
temperature = 0.7
seed = 42

[judge]
kind = "server"
repo_id = "other/model"
revision = "def4567890abc123"
quant = "Q5_K_M"
family = "other"
base_url = "http://127.0.0.1:1234/v1"
structured_method = "tools"
parallel_tool_calls = true
reasoning_handling = "enabled"
context_window = 8000
temperature = 0.7
seed = 42

[fallback]
kind = "server"
repo_id = "fallback/model"
revision = "xyz1234567890abc"
quant = "Q4_K_M"
family = "qwen"
base_url = "http://127.0.0.1:1234/v1"
structured_method = "json_schema"
parallel_tool_calls = false
reasoning_handling = "disabled"
context_window = 4000
temperature = 0.5
seed = 42

[fake]
kind = "fake"
family = "fake"
structured_method = "tools"
temperature = 0.7
seed = 42
"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = Path(tmpdir) / "models.toml"
        config_file.write_text(toml_content)
        load_models_config(config_file)

        model = cast(ChatOpenAI, build_chat_model("primary"))

        # Track what method was requested
        called_methods: list[str] = []

        def mock_with_structured(schema: Any, **kwargs: Any) -> Any:
            method = kwargs.get("method", "unknown")
            called_methods.append(method)

            # Create a mock runnable that returns the instance
            instance = SimpleSchema(name="test", value=42)
            mock_response = MagicMock()
            mock_response.invoke.return_value = instance
            return mock_response

        # Patch ChatOpenAI.with_structured_output at the class level
        with patch.object(type(model), "with_structured_output", side_effect=mock_with_structured):
            # Call structured_output
            result = structured_output(model, SimpleSchema, "Extract test data")

        # Verify no tools method was called
        assert "tools" not in called_methods
        # Verify json_schema was used
        assert "json_schema" in called_methods
        assert isinstance(result, SimpleSchema)


def test_tool_call_failure_falls_back_to_json_schema_exactly_once() -> None:
    """AC5: Tool call failure falls back to JSON schema exactly once."""
    toml_content = """
[primary]
kind = "server"
repo_id = "unsloth/Qwen3-30B-A3B-Instruct-2507-GGUF"
revision = "abc1234567890def"
quant = "Q4_K_M"
family = "qwen"
base_url = "http://127.0.0.1:1234/v1"
structured_method = "tools"
parallel_tool_calls = true
reasoning_handling = "enabled"
context_window = 8000
temperature = 0.7
seed = 42

[judge]
kind = "server"
repo_id = "other/model"
revision = "def4567890abc123"
quant = "Q5_K_M"
family = "other"
base_url = "http://127.0.0.1:1234/v1"
structured_method = "tools"
parallel_tool_calls = true
reasoning_handling = "enabled"
context_window = 8000
temperature = 0.7
seed = 42

[fallback]
kind = "server"
repo_id = "fallback/model"
revision = "xyz1234567890abc"
quant = "Q4_K_M"
family = "qwen"
base_url = "http://127.0.0.1:1234/v1"
structured_method = "json_schema"
parallel_tool_calls = false
reasoning_handling = "disabled"
context_window = 4000
temperature = 0.5
seed = 42

[fake]
kind = "fake"
family = "fake"
structured_method = "tools"
temperature = 0.7
seed = 42
"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = Path(tmpdir) / "models.toml"
        config_file.write_text(toml_content)
        load_models_config(config_file)

        model = cast(ChatOpenAI, build_chat_model("primary"))

        # Track call attempts
        called_methods: list[str] = []

        def mock_with_structured(schema: Any, **kwargs: Any) -> Any:
            method = kwargs.get("method", "unknown")
            called_methods.append(method)

            # First call (function_calling) should fail
            if method == "function_calling":
                mock_response = MagicMock()
                mock_response.invoke.side_effect = Exception("Tool calling failed")
                return mock_response
            # Second call (json_schema) should succeed
            elif method == "json_schema":
                instance = SimpleSchema(name="test", value=42)
                mock_response = MagicMock()
                mock_response.invoke.return_value = instance
                return mock_response
            else:
                raise AssertionError(f"Unexpected method: {method}")

        # Patch ChatOpenAI.with_structured_output at the class level
        with patch.object(type(model), "with_structured_output", side_effect=mock_with_structured):
            # Call structured_output
            result = structured_output(model, SimpleSchema, "Extract test data")

        # Verify result is correct
        assert isinstance(result, SimpleSchema)
        # Verify exactly 2 attempts were made: function_calling first, then json_schema
        assert called_methods == ["function_calling", "json_schema"]
        assert len(called_methods) == 2
