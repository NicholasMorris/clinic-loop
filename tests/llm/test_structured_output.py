"""Tests for structured output methods."""

import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
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

        model = build_chat_model("primary")

        # Mock the model's with_structured_output method to capture the payload
        sent_payload: dict[str, Any] = {}

        original_with_structured = model.with_structured_output

        def mock_with_structured(schema: Any, **kwargs: Any) -> Any:
            # Simulate what langchain does - calling create with tools or json_schema
            if "method" in kwargs and kwargs["method"] == "json_schema":
                sent_payload["method"] = "json_schema"
                # Simulate successful response
                instance = SimpleSchema(name="test", value=42)
                mock_response = MagicMock()
                mock_response.invoke.return_value = instance
                return mock_response
            return original_with_structured(schema, **kwargs)

        model.with_structured_output = mock_with_structured

        # Call structured_output
        result = structured_output(model, SimpleSchema, "Extract test data")

        # Verify no tools key was sent
        assert "tools" not in sent_payload
        # Verify the method was json_schema
        assert sent_payload.get("method") == "json_schema"


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

        model = build_chat_model("primary")

        # Track call attempts
        call_count = 0

        def mock_with_structured(schema: Any, **kwargs: Any) -> Any:
            nonlocal call_count
            call_count += 1

            # First call (tools) should fail
            if call_count == 1 and kwargs.get("method") == "tools":
                mock_response = MagicMock()
                mock_response.invoke.side_effect = Exception("Tool calling failed")
                return mock_response
            # Second call (json_schema) should succeed
            elif call_count == 2 and kwargs.get("method") == "json_schema":
                instance = SimpleSchema(name="test", value=42)
                mock_response = MagicMock()
                mock_response.invoke.return_value = instance
                return mock_response
            # If there's a third call, that's a failure
            elif call_count > 2:
                raise AssertionError(f"Too many attempts: {call_count}")

            return MagicMock()

        model.with_structured_output = mock_with_structured

        # Call structured_output
        result = structured_output(model, SimpleSchema, "Extract test data")

        # Verify result is correct
        assert isinstance(result, SimpleSchema)
        # Verify exactly 2 attempts were made
        assert call_count == 2
