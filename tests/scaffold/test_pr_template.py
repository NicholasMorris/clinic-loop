"""Tests for PR template and Makefile targets."""

from pathlib import Path


def get_pr_template_path() -> Path:
    """Get the path to PR template."""
    return Path(__file__).parent.parent.parent / ".github" / "PULL_REQUEST_TEMPLATE.md"


def get_makefile_path() -> Path:
    """Get the path to Makefile."""
    return Path(__file__).parent.parent.parent / "Makefile"


def get_gitignore_path() -> Path:
    """Get the path to .gitignore."""
    return Path(__file__).parent.parent.parent / ".gitignore"


def test_template_fields_setup_targets_and_gitignore_entries() -> None:
    """Test PR template, Makefile targets, and .gitignore.

    AC7: .github/PULL_REQUEST_TEMPLATE.md contains fields labelled for
    the red-commit SHA, the files globs and the docs-and-fragment entry;
    the Makefile declares doctor and setup targets whose recipes invoke
    python -m clinicloop.setup.doctor and python -m clinicloop.setup.install;
    and .gitignore contains the entries data/, runs/, corpus/rendered/,
    .venv and evals/local/, asserted as an exact membership check so
    later issues add none.
    """
    # Check PR template
    pr_template_path = get_pr_template_path()
    assert pr_template_path.exists(), f"PR template not found at {pr_template_path}"

    template_content = pr_template_path.read_text()

    # Check for required fields
    assert "red-commit" in template_content.lower() or "red commit" in template_content.lower(), (
        "PR template should contain 'red-commit' field"
    )

    assert "files" in template_content.lower() or "glob" in template_content.lower(), (
        "PR template should contain 'files' or 'glob' field"
    )

    template_lower = template_content.lower()
    has_doc_field = (
        "doc" in template_lower or "changelog" in template_lower or "fragment" in template_lower
    )
    assert has_doc_field, "PR template should contain documentation/changelog field"

    # Check Makefile targets
    makefile_path = get_makefile_path()
    assert makefile_path.exists(), "Makefile not found"

    makefile_content = makefile_path.read_text()

    # Check for doctor target
    assert ".PHONY: doctor" in makefile_content or "doctor:" in makefile_content, (
        "Makefile should declare doctor target"
    )
    assert "python -m clinicloop.setup.doctor" in makefile_content, (
        "doctor target should invoke python -m clinicloop.setup.doctor"
    )

    # Check for setup target
    assert ".PHONY: setup" in makefile_content or "setup:" in makefile_content, (
        "Makefile should declare setup target"
    )
    assert "python -m clinicloop.setup.install" in makefile_content, (
        "setup target should invoke python -m clinicloop.setup.install"
    )

    # Check .gitignore entries
    gitignore_path = get_gitignore_path()
    assert gitignore_path.exists(), f".gitignore not found at {gitignore_path}"

    gitignore_content = gitignore_path.read_text()
    gitignore_lines = set(
        line.strip()
        for line in gitignore_content.split("\n")
        if line.strip() and not line.strip().startswith("#")
    )

    required_entries = {"data/", "runs/", "corpus/rendered/", ".venv", "evals/local/"}
    for entry in required_entries:
        assert entry in gitignore_lines, f"'{entry}' not found in .gitignore"
