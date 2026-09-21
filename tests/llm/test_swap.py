"""Tests for model factory attribute copying."""

import tempfile
from pathlib import Path

from clinicloop.llm.config import load_models_config
from clinicloop.llm.factory import build_chat_model


def test_every_model_attribute_comes_from_the_config_row() -> None:
    """AC6: Every model attribute comes from config, and models differ as expected."""
    # First fixture
    toml_fixture1 = """
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
        config_file.write_text(toml_fixture1)
        load_models_config(config_file)

        built1 = build_chat_model("primary")

        assert built1.model_name == "unsloth/Qwen3-30B-A3B-Instruct-2507-GGUF"
        assert built1.openai_api_base == "http://127.0.0.1:1234/v1"
        assert built1.temperature == 0.7

    # Second fixture with different values
    toml_fixture2 = """
[primary]
kind = "server"
repo_id = "different/model"
revision = "def4567890abc123"
quant = "Q5_K_M"
family = "other"
base_url = "http://127.0.0.1:5678/v1"
structured_method = "json_schema"
parallel_tool_calls = false
reasoning_handling = "disabled"
context_window = 4000
temperature = 0.5
seed = 99

[judge]
kind = "server"
repo_id = "judge/model"
revision = "xyz1234567890abc"
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
repo_id = "fallback/model"
revision = "abc1234567890def"
quant = "Q4_K_M"
family = "fallback"
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
        config_file.write_text(toml_fixture2)
        load_models_config(config_file)

        built2 = build_chat_model("primary")

        assert built2.model_name == "different/model"
        assert built2.openai_api_base == "http://127.0.0.1:5678/v1"
        assert built2.temperature == 0.5

        # Verify the two models differ
        assert built1.model_name != built2.model_name
        assert built1.openai_api_base != built2.openai_api_base
