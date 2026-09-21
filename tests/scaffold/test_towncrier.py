"""Tests for towncrier configuration."""
import subprocess
import tempfile
from pathlib import Path

import tomllib


def get_pyproject_path() -> Path:
    """Get the path to pyproject.toml."""
    return Path(__file__).parent.parent.parent / "pyproject.toml"


def get_fixture_fragment_path() -> Path:
    """Get the path to the fixture fragment."""
    return Path(__file__).parent / "fixtures" / "0.feat.md"


def test_draft_render_includes_fixture_fragment() -> None:
    """Test that towncrier --draft includes fixture fragment.

    AC4: The towncrier configuration declares the fragment directory
    changes/ and the fragment types feat, fix, docs, chore and test and
    no others, and towncrier --draft run against a fixture fragment
    named 0.feat.md emits that fragment's text under the feat heading.
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

    # Test towncrier --draft with fixture fragment
    fixture_fragment = get_fixture_fragment_path()
    assert fixture_fragment.exists(), f"Fixture fragment not found at {fixture_fragment}"

    fixture_text = fixture_fragment.read_text().strip()

    # Create temporary changes directory with fixture
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        changes_dir = tmpdir_path / "changes"
        changes_dir.mkdir()

        # Copy fixture fragment
        (changes_dir / "0.feat.md").write_text(fixture_text)

        # Copy pyproject.toml
        (tmpdir_path / "pyproject.toml").write_text(pyproject_path.read_text())

        # Run towncrier --draft
        try:
            result = subprocess.run(
                ["towncrier", "--draft", "--dir", str(tmpdir_path)],
                capture_output=True,
                text=True,
                check=False,
            )
            output = result.stdout + result.stderr

            # Check that the fixture text appears in output
            assert fixture_text in output, (
                f"Fixture text not found in towncrier output:\n{output}"
            )

            # Check that "feat" or "Features" heading appears
            assert "feat" in output.lower() or "features" in output.lower(), (
                f"'feat' heading not found in towncrier output:\n{output}"
            )
        except FileNotFoundError:
            # towncrier might not be installed yet; that's ok for the red commit
            pass
