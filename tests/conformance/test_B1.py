"""AC6: Repository conformance with Python 3.12, clinicloop package, and public repo settings."""

import json
import sys
from pathlib import Path

import pytest


@pytest.mark.checklist_id("B1")
def test_repository_payload_is_public_python_3_12_clinicloop() -> None:
    """Test that repo is public, using Python 3.12, and package name is clinicloop."""
    # Check Python version
    assert sys.version_info[:2] == (3, 12), \
        f"Expected Python 3.12, got {sys.version_info[0]}.{sys.version_info[1]}"

    # Check installed distribution name
    try:
        import clinicloop  # noqa: F401
    except ImportError:
        pytest.fail("Package 'clinicloop' not installed")

    # Check repo settings from recorded payload
    repo_settings_path = Path(__file__).parent / "data" / "repo_settings.json"
    assert repo_settings_path.exists(), f"Repo settings file not found at {repo_settings_path}"

    with open(repo_settings_path) as f:
        repo_settings = json.load(f)

    assert repo_settings["visibility"] == "public", \
        f"Expected public repo, got visibility={repo_settings['visibility']}"
    assert repo_settings["name"] == "clinic-loop", \
        f"Expected repo name 'clinic-loop', got {repo_settings['name']}"
    assert repo_settings["default_branch"] == "main", \
        f"Expected default_branch 'main', got {repo_settings['default_branch']}"
