"""Conformance test for D2: MkDocs builds in strict mode."""

import subprocess
from pathlib import Path

import pytest


@pytest.mark.checklist_id("D2")
def test_site_builds_strict() -> None:
    """Test that mkdocs build --strict exits 0 on the committed tree.

    D2: MkDocs Material built and published via GitHub Pages (USER RULING:
    from a local build pushed to gh-pages, no CI).
    """
    repo_root = Path(__file__).parent.parent.parent

    result = subprocess.run(
        ["uv", "run", "--extra", "docs", "mkdocs", "build", "--strict"],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, \
        f"mkdocs build --strict failed with exit code {result.returncode}\n{result.stderr}"
