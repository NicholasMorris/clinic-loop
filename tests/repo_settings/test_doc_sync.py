"""Tests for documentation and checker expectation synchronization."""

import sys
from pathlib import Path
from typing import Any

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from repo_settings.review_contexts import (  # type: ignore
    REQUIRED_STATUS_CONTEXTS,
    REQUIRED_TOKEN_SCOPES,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
DOCS_FILE = REPO_ROOT / "docs" / "process" / "repository-settings.md"


def test_doc_and_checker_expectations_match() -> None:
    """AC6: Documentation and checker expectations are synchronized.

    The docs/process/repository-settings.md file must record:
    - visibility: public
    - repository name: clinic-loop
    - default branch: main
    - Pages build type: legacy
    - The six required status contexts
    - The two required token scopes

    The test parses the document and asserts the parsed values match the checker's
    declared expectations.
    """
    assert DOCS_FILE.exists(), f"Documentation file not found: {DOCS_FILE}"

    doc_content = DOCS_FILE.read_text()

    # Parse expectations from the document
    expectations: dict[str, Any] = {}

    # Look for visibility setting
    if "visibility" in doc_content and "public" in doc_content:
        expectations["visibility"] = "public"

    # Look for repository name
    if "clinic-loop" in doc_content:
        expectations["repo_name"] = "clinic-loop"

    # Look for default branch
    if "default branch" in doc_content and "main" in doc_content:
        expectations["default_branch"] = "main"

    # Look for Pages settings
    if "legacy" in doc_content and "gh-pages" in doc_content:
        expectations["pages_build_type"] = "legacy"
        expectations["pages_source_branch"] = "gh-pages"

    # Look for required status contexts
    if "status_contexts" not in expectations:
        expectations["status_contexts"] = []
    for context in REQUIRED_STATUS_CONTEXTS:
        if context in doc_content:
            expectations["status_contexts"].append(context)

    # Look for required token scopes
    if "token_scopes" not in expectations:
        expectations["token_scopes"] = []
    for scope in REQUIRED_TOKEN_SCOPES:
        if scope in doc_content:
            expectations["token_scopes"].append(scope)

    # Verify all expected values are present
    assert expectations.get("visibility") == "public", (
        "Documentation must record visibility as public"
    )
    assert expectations.get("repo_name") == "clinic-loop", (
        "Documentation must record repository name as clinic-loop"
    )
    assert expectations.get("default_branch") == "main", (
        "Documentation must record default branch as main"
    )
    assert expectations.get("pages_build_type") == "legacy", (
        "Documentation must record Pages build type as legacy"
    )
    assert expectations.get("pages_source_branch") == "gh-pages", (
        "Documentation must record Pages source branch as gh-pages"
    )

    # Verify all required status contexts are mentioned
    doc_contexts = set(expectations.get("status_contexts", []))
    expected_contexts = set(REQUIRED_STATUS_CONTEXTS)
    assert doc_contexts == expected_contexts, (
        f"Documentation must mention all required contexts. "
        f"Expected {expected_contexts}, found {doc_contexts}"
    )

    # Verify all required token scopes are mentioned
    doc_scopes = set(expectations.get("token_scopes", []))
    expected_scopes = set(REQUIRED_TOKEN_SCOPES)
    assert doc_scopes == expected_scopes, (
        f"Documentation must mention all required scopes. "
        f"Expected {expected_scopes}, found {doc_scopes}"
    )
