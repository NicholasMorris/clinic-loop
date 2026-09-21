"""D5: Required documentation pages exist and are navigable."""

from pathlib import Path

import pytest


@pytest.mark.checklist_id("D5")
def test_required_documentation_pages_exist() -> None:
    """Test that four required stub pages exist with the placeholder marker.

    D5: docs/problem-inventory.md, docs/integrity-ethics.md, docs/evaluation.md
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

    # Verify pages are reachable from navigation
    nav_path = docs_dir / ".nav.yml"
    assert nav_path.exists(), "docs/.nav.yml must exist for navigation"

    nav_content = nav_path.read_text(encoding="utf-8")

    # Verify all required pages are mentioned in navigation
    for page_name in ["problem-inventory.md", "integrity-ethics.md", "evaluation.md", "runbook.md"]:
        assert page_name in nav_content or page_name[:-3] in nav_content, (
            f"Required page {page_name} not found in navigation"
        )
