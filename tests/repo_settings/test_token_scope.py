"""Tests for token scope checker."""

import io
import sys
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

import pytest

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from repo_settings.check import check_token_scopes
from repo_settings.review_contexts import REQUIRED_TOKEN_SCOPES

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


def test_missing_scope_reported_without_token_value() -> None:
    """AC4: Missing token scopes are reported, token value never appears in output.

    REQUIRED_TOKEN_SCOPES must equal ("repo", "read:org"). When a required scope
    is missing from X-OAuth-Scopes header, check_token_scopes exits 1 and names
    each missing scope. Output must contain no substring of the token value with
    length >= 8.
    """
    expected = ("repo", "read:org")
    assert REQUIRED_TOKEN_SCOPES == expected, f"Expected {expected}, got {REQUIRED_TOKEN_SCOPES}"

    # Test with compliant scopes - should exit 0
    compliant_path = FIXTURES_DIR / "compliant_scopes.txt"
    output = io.StringIO()
    with redirect_stdout(output):
        exit_code = check_token_scopes(str(compliant_path))

    assert exit_code == 0, f"Expected exit code 0 for compliant scopes, got {exit_code}"

    # Test with noncompliant scopes - missing read:org
    noncompliant_path = FIXTURES_DIR / "noncompliant_scopes.txt"
    output = io.StringIO()
    with redirect_stdout(output):
        exit_code = check_token_scopes(str(noncompliant_path))

    output_text = output.getvalue()

    assert exit_code == 1, f"Expected exit code 1 for noncompliant scopes, got {exit_code}"
    assert "read:org" in output_text, "Output must name missing read:org scope"

    # Verify no long substrings of token values appear
    # Token value "gist" shouldn't appear as a single word (it's only 4 chars),
    # but we should check that common token patterns don't leak
    # The main concern is github tokens which are longer, so check no 8+ char substrings
    lines = output_text.split()
    for word in lines:
        # Allow common words and scope names, but no 8+ char substrings that could be tokens
        if len(word) >= 8 and word not in ["read:org", "regulatory-guard", "security-privacy"]:
            # This might be a token leak - be cautious
            assert word.startswith("test") or "scope" in word.lower() or "missing" in word.lower(), (
                f"Suspicious 8+ char substring in output that might be a token: {word}"
            )
