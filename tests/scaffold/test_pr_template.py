"""Tests for the pull request template, the setup targets and the .gitignore entries."""

import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

REQUIRED_IGNORES = {"data/", "runs/", "corpus/rendered/", ".venv", "evals/local/"}
ORDINARY_IGNORES = {
    "__pycache__/",
    "*.py[cod]",
    "*.egg-info/",
    ".pytest_cache/",
    ".mypy_cache/",
    ".ruff_cache/",
    ".coverage",
    "htmlcov/",
    "dist/",
    "site/",
    ".DS_Store",
}


def headings(markdown: str) -> list[str]:
    """Return the lower-cased Markdown headings of a document.

    Args:
        markdown: The document text.

    Returns:
        Heading texts in document order.
    """
    return [m.group(1).strip().lower() for m in re.finditer(r"^#{1,6}\s+(.+)$", markdown, re.M)]


def make_dry_run(target: str) -> str:
    """Return the commands make would run for a target.

    Args:
        target: The make target.

    Returns:
        The dry-run output.
    """
    result = subprocess.run(
        ["make", "-n", "-C", str(REPO_ROOT), target], capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, f"make -n {target} failed: {result.stderr}"
    return result.stdout


def test_template_fields_setup_targets_and_gitignore_entries() -> None:
    """AC7: template fields, doctor and setup recipes, and exact .gitignore membership."""
    template = (REPO_ROOT / ".github" / "PULL_REQUEST_TEMPLATE.md").read_text()
    titles = headings(template)
    assert any("red-commit sha" in title for title in titles), f"no red-commit SHA field: {titles}"
    assert any("files" in title and "glob" in title for title in titles), (
        f"no files globs field: {titles}"
    )
    assert any("docs" in title and "fragment" in title for title in titles), (
        f"no docs-and-fragment field: {titles}"
    )

    assert "python -m clinicloop.setup.doctor" in make_dry_run("doctor")
    assert "python -m clinicloop.setup.install" in make_dry_run("setup")

    lines = {
        line.strip()
        for line in (REPO_ROOT / ".gitignore").read_text().splitlines()
        if line.strip() and not line.strip().startswith("#")
    }
    assert REQUIRED_IGNORES <= lines, f"missing entries: {REQUIRED_IGNORES - lines}"
    extra = lines - ORDINARY_IGNORES - REQUIRED_IGNORES
    assert not extra, f"unexpected entries beyond the five declared: {extra}"
    assert "uv.lock" not in lines, "uv.lock must not be ignored"
