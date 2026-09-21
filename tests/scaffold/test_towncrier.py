"""Tests for the towncrier changelog configuration."""

import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_FRAGMENT = Path(__file__).resolve().parent / "fixtures" / "0.feat.md"
EXPECTED_TYPES = ["feat", "fix", "docs", "chore", "test"]


def test_draft_render_includes_fixture_fragment(tmp_path: Path) -> None:
    """AC4: towncrier config declares changes/ and five types, and renders the fixture."""
    with open(REPO_ROOT / "pyproject.toml", "rb") as handle:
        config = tomllib.load(handle)["tool"]["towncrier"]

    assert config["directory"] == "changes", "fragment directory must be changes/"
    declared = set(config["fragment"])
    assert declared == set(EXPECTED_TYPES), f"fragment types must be exactly {EXPECTED_TYPES}"

    project = tmp_path / "project"
    (project / "changes").mkdir(parents=True)
    shutil.copy(REPO_ROOT / "pyproject.toml", project / "pyproject.toml")
    shutil.copy(FIXTURE_FRAGMENT, project / "changes" / FIXTURE_FRAGMENT.name)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "towncrier",
            "build",
            "--draft",
            "--version",
            "0.0.0",
            "--dir",
            str(project),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, f"towncrier failed: {result.stdout}\n{result.stderr}"

    fixture_text = FIXTURE_FRAGMENT.read_text().strip()
    assert fixture_text, "fixture fragment is empty"
    draft = result.stdout
    assert fixture_text in draft, f"fixture text missing from draft:\n{draft}"

    heading = draft.index("Features")
    position = draft.index(fixture_text)
    assert heading < position, "fixture text is not below the Features heading"
    assert "###" not in draft[heading + len("Features") : position], "another heading intervenes"
