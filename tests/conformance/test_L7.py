"""L7: Single models.toml config; swapping models requires no agent code changes.

Tests that agent code is decoupled from model selection via the factory and config
loader. Changing models.toml values (repo_id, base_url, temperature) should not
require edits to agent code.
"""

import tempfile
from pathlib import Path
from typing import cast

import pytest
from langchain_openai import ChatOpenAI

from clinicloop.llm.config import load_models_config
from clinicloop.llm.factory import build_chat_model


@pytest.mark.checklist_id("L7")
def test_swapping_models_via_config_needs_no_code_changes() -> None:
    """L7: Agent code is unchanged when swapping models through models.toml."""
    # Fixture 1: Qwen model at default port
    toml_fixture_1 = """
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
temperature = 0.7
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
        config_file.write_text(toml_fixture_1)
        load_models_config(config_file)

        # Agent code: factory call is identical in all configs
        model_1 = cast(ChatOpenAI, build_chat_model("primary"))

        # Capture config-driven attributes
        repo_id_1 = model_1.model_name
        base_url_1 = model_1.openai_api_base
        temp_1 = model_1.temperature

    # Fixture 2: Different model at different port with different temperature
    toml_fixture_2 = """
[primary]
kind = "server"
repo_id = "different-vendor/some-model-24B"
revision = "fedcba9876543210"
quant = "Q6_K"
family = "custom"
base_url = "http://127.0.0.1:9876/v1"
structured_method = "json_schema"
parallel_tool_calls = false
reasoning_handling = "disabled"
context_window = 6000
temperature = 0.3
seed = 123

[judge]
kind = "server"
repo_id = "judge/model"
revision = "abc1234567890def"
quant = "Q4_K_M"
family = "judge"
base_url = "http://127.0.0.1:1234/v1"
structured_method = "tools"
parallel_tool_calls = true
reasoning_handling = "enabled"
context_window = 8000
temperature = 0.7
seed = 42

[fallback]
kind = "server"
repo_id = "fallback/model-v2"
revision = "987654321fedcba0"
quant = "Q4_K_M"
family = "fallback"
base_url = "http://127.0.0.1:1234/v1"
structured_method = "json_schema"
parallel_tool_calls = false
reasoning_handling = "disabled"
context_window = 4000
temperature = 0.7
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
        config_file.write_text(toml_fixture_2)
        load_models_config(config_file)

        # Agent code: identical call, new config provides all differences
        model_2 = cast(ChatOpenAI, build_chat_model("primary"))

        # Capture config-driven attributes from fixture 2
        repo_id_2 = model_2.model_name
        base_url_2 = model_2.openai_api_base
        temp_2 = model_2.temperature

    # Verify models are different across configs
    assert repo_id_1 != repo_id_2, "Models should have different repo IDs"
    assert base_url_1 != base_url_2, "Models should have different base URLs"
    assert temp_1 != temp_2, "Models should have different temperatures"

    # Verify each model has the correct config attributes
    assert repo_id_1 == "unsloth/Qwen3-30B-A3B-Instruct-2507-GGUF"
    assert base_url_1 == "http://127.0.0.1:1234/v1"
    assert temp_1 == 0.7

    assert repo_id_2 == "different-vendor/some-model-24B"
    assert base_url_2 == "http://127.0.0.1:9876/v1"
    assert temp_2 == 0.3
