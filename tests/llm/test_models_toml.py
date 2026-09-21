"""Tests for models.toml loading and validation."""

import tempfile
from pathlib import Path

import pytest
from pydantic import ValidationError

from clinicloop.llm.config import (
    FakeRowHasServerFields,
    NonLoopbackBaseURL,
    load_models_config,
)


def test_non_loopback_base_url_rejected() -> None:
    """AC1: load_models_config raises NonLoopbackBaseURL for non-loopback addresses."""
    toml_content = """
[primary]
kind = "server"
repo_id = "unsloth/Qwen3-30B-A3B-Instruct-2507-GGUF"
revision = "abc1234567890def"
quant = "Q4_K_M"
family = "qwen"
base_url = "http://192.168.1.100:1234/v1"
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

        with pytest.raises(NonLoopbackBaseURL) as exc_info:
            load_models_config(config_file)

        # Exception message should contain the offending role name
        assert "primary" in str(exc_info.value).lower()


def test_server_row_pinning_rules_and_fake_row_field_rules() -> None:
    """AC2: Server row validation and fake row field rules."""
    # Test missing required server field
    toml_missing_field = """
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
        config_file.write_text(toml_missing_field)

        with pytest.raises(ValidationError) as exc_info_missing:
            load_models_config(config_file)

        # Should name the missing field
        assert "seed" in str(exc_info_missing.value).lower()

    # Test revision = "main" (should fail)
    toml_main_revision = """
[primary]
kind = "server"
repo_id = "unsloth/Qwen3-30B-A3B-Instruct-2507-GGUF"
revision = "main"
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
        config_file.write_text(toml_main_revision)

        with pytest.raises(ValidationError) as exc_info_revision:
            load_models_config(config_file)

        assert "revision" in str(exc_info_revision.value).lower()

    # Test quant = "" (should fail)
    toml_empty_quant = """
[primary]
kind = "server"
repo_id = "unsloth/Qwen3-30B-A3B-Instruct-2507-GGUF"
revision = "abc1234567890def"
quant = ""
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
        config_file.write_text(toml_empty_quant)

        with pytest.raises(ValidationError) as exc_info_quant:
            load_models_config(config_file)

        assert "quant" in str(exc_info_quant.value).lower()

    # Test fake row with repo_id (should fail)
    toml_fake_with_repo_id = """
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
repo_id = "should/not/have/this"
family = "fake"
structured_method = "tools"
temperature = 0.7
seed = 42
"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = Path(tmpdir) / "models.toml"
        config_file.write_text(toml_fake_with_repo_id)

        with pytest.raises(FakeRowHasServerFields) as exc_info_fake:
            load_models_config(config_file)

        # Should name the offending field
        assert "repo_id" in str(exc_info_fake.value).lower()
