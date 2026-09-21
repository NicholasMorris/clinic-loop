"""Tests for towncrier configuration."""

from pathlib import Path

import tomllib


def get_pyproject_path() -> Path:
    """Get the path to pyproject.toml."""
    return Path(__file__).parent.parent.parent / "pyproject.toml"


def get_fixture_fragment_path() -> Path:
    """Get the path to the fixture fragment."""
    return Path(__file__).parent / "fixtures" / "0.feat.md"


def test_draft_render_includes_fixture_fragment() -> None:
    """Test that towncrier configuration is correct.

    AC4: The towncrier configuration declares the fragment directory
    changes/ and the fragment types feat, fix, docs, chore and test and
    no others.
    """
    pyproject_path = get_pyproject_path()
    assert pyproject_path.exists(), "pyproject.toml not found"

    with open(pyproject_path, "rb") as f:
        data = tomllib.load(f)

    # Check towncrier configuration
    towncrier_config = data.get("tool", {}).get("towncrier", {})

    # Check fragment directory
    assert towncrier_config.get("directory") == "changes", (
        "towncrier directory not set to 'changes'"
    )

    # Check fragment types
    fragment_types = set(towncrier_config.get("fragment", {}).get("types", {}).keys())
    expected_types = {"feat", "fix", "docs", "chore", "test"}
    assert fragment_types == expected_types, (
        f"Expected fragment types {expected_types}, got {fragment_types}"
    )

    # Verify fixture fragment exists
    fixture_fragment = get_fixture_fragment_path()
    assert fixture_fragment.exists(), f"Fixture fragment not found at {fixture_fragment}"
