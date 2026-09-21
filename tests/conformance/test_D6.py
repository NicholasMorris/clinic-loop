"""AC7: Lint and type checks pass with Google-style docstring rules."""

import subprocess
import tomllib
from pathlib import Path

import pytest


@pytest.mark.checklist_id("D6")
def test_lint_and_types_pass_with_google_docstring_rules() -> None:
    """Test that ruff and mypy pass with Google-style docstrings configured."""
    # Check ruff configuration
    pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"
    assert pyproject_path.exists(), f"pyproject.toml not found at {pyproject_path}"

    with open(pyproject_path, "rb") as f:
        pyproject = tomllib.load(f)

    ruff_config = pyproject.get("tool", {}).get("ruff", {})
    ruff_lint = ruff_config.get("lint", {})

    # Check that D rule set is selected
    selected_rules = ruff_lint.get("select", [])
    assert "D" in selected_rules, f"D rule set not selected in ruff config. Got: {selected_rules}"

    # Check that google convention is set
    pydocstyle = ruff_lint.get("pydocstyle", {})
    convention = pydocstyle.get("convention")
    assert convention == "google", f"Expected google docstring convention, got: {convention}"

    # Run ruff check on src/ and tests/
    result = subprocess.run(
        ["python", "-m", "ruff", "check", "src", "tests"],
        cwd=pyproject_path.parent,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"ruff check failed:\n{result.stdout}\n{result.stderr}"

    # Run mypy on src/ and tests/
    result = subprocess.run(
        ["python", "-m", "mypy"],
        cwd=pyproject_path.parent,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"mypy failed:\n{result.stdout}\n{result.stderr}"
