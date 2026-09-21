"""L2: Loopback constraint for LM Studio server.

Tests that all server rows in models.toml use loopback addresses only (127.0.0.1,
::1, or localhost), and that the factory and structured output code enforce this
at configuration time.
"""

import tempfile
from pathlib import Path

import pytest

from clinicloop.llm.config import NonLoopbackBaseURL, load_models_config


@pytest.mark.checklist_id("L2")
def test_all_model_rows_require_loopback_base_url() -> None:
    """L2: All server rows must have loopback base_url (127.0.0.1, ::1, localhost)."""
    # Valid loopback URLs should load without error
    toml_loopback = """
[primary]
kind = "server"
repo_id = "test/model"
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
repo_id = "test/judge"
revision = "def4567890abc123"
quant = "Q4_K_M"
family = "judge"
base_url = "http://localhost:1234/v1"
structured_method = "tools"
parallel_tool_calls = true
reasoning_handling = "enabled"
context_window = 8000
temperature = 0.7
seed = 42

[fallback]
kind = "server"
repo_id = "test/fallback"
revision = "xyz1234567890abc"
quant = "Q4_K_M"
family = "qwen"
base_url = "http://[::1]:1234/v1"
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
        config_file.write_text(toml_loopback)
        config = load_models_config(config_file)
        # Should load successfully
        assert config.primary.base_url == "http://127.0.0.1:1234/v1"

    # Non-loopback URLs should raise NonLoopbackBaseURL
    toml_non_loopback = """
[primary]
kind = "server"
repo_id = "test/model"
revision = "abc1234567890def"
quant = "Q4_K_M"
family = "qwen"
base_url = "http://example.com:1234/v1"
structured_method = "tools"
parallel_tool_calls = true
reasoning_handling = "enabled"
context_window = 8000
temperature = 0.7
seed = 42

[judge]
kind = "server"
repo_id = "test/judge"
revision = "def4567890abc123"
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
repo_id = "test/fallback"
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
        config_file.write_text(toml_non_loopback)
        with pytest.raises(NonLoopbackBaseURL) as exc_info:
            load_models_config(config_file)
        assert "primary" in str(exc_info.value).lower()
