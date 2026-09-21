"""Tests for MkDocs build in strict mode."""

import tempfile
from pathlib import Path

from tests.docs.helpers import build_site


def test_strict_build_fails_on_broken_internal_link() -> None:
    """Test that mkdocs build --strict exits 0 on committed tree.

    Also verify it exits non-zero when a fixture page with a broken link is added.

    AC1: mkdocs build --strict exits 0 on the committed tree, and exits non-zero
    when a fixture page containing a link to a non-existent document is added
    to a temporary copy of the docs tree.
    """
    # Find the docs directory in the repository root
    repo_root = Path(__file__).parent.parent.parent
    docs_dir = repo_root / "docs"

    # Test 1: Committed tree should build successfully with strict mode
    exit_code = build_site(docs_dir, strict=True)
    assert exit_code == 0, f"mkdocs build --strict should exit 0, got {exit_code}"

    # Test 2: Adding a fixture page with broken link should fail
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        # Copy the docs directory to temp location
        import shutil

        tmp_docs = tmp_path / "docs"
        shutil.copytree(docs_dir, tmp_docs)

        # Create a fixture page with a broken link
        fixture_page = tmp_docs / "fixture-broken-link.md"
        fixture_page.write_text(
            "# Fixture Page with Broken Link\n\n[Link to non-existent page](./non-existent.md)\n"
        )

        # Build should fail with the broken link
        exit_code = build_site(tmp_docs, strict=True)
        assert exit_code != 0, "mkdocs build --strict should fail with broken link"
