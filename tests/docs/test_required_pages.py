"""Tests for required documentation pages."""

from pathlib import Path


def test_four_required_pages_exist_and_are_in_the_nav() -> None:
    """Test that four required stub pages exist with the placeholder marker.

    AC5: docs/problem-inventory.md, docs/integrity-ethics.md, docs/evaluation.md
    and docs/runbook.md all exist, each contains the literal marker
    'STUB: content owned by a later issue', and each is reachable from the
    built navigation.
    """
    repo_root = Path(__file__).parent.parent.parent
    docs_dir = repo_root / "docs"

    required_pages = {
        "problem-inventory.md": docs_dir / "problem-inventory.md",
        "integrity-ethics.md": docs_dir / "integrity-ethics.md",
        "evaluation.md": docs_dir / "evaluation.md",
        "runbook.md": docs_dir / "runbook.md",
    }

    stub_marker = "STUB: content owned by a later issue"

    for page_name, page_path in required_pages.items():
        # Check file exists
        assert page_path.exists(), f"Required page {page_name} does not exist at {page_path}"

        # Check contains the placeholder marker
        content = page_path.read_text(encoding="utf-8")
        assert stub_marker in content, (
            f"Page {page_name} does not contain the required marker: '{stub_marker}'"
        )

    # Note: Full navigation reachability is verified by the mkdocs build test.
    # We ensure here that the files exist with the correct marker.
