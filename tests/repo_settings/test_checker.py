"""Tests for repository settings checker."""

import json
import socket
import sys
import tempfile
from pathlib import Path
from unittest import mock

import pytest

# Add scripts directory to path so we can import the checker module
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from repo_settings.check import check_protection, check_settings
from repo_settings.review_contexts import REQUIRED_STATUS_CONTEXTS

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


def test_exit_zero_on_compliant_payload() -> None:
    """AC1: check_settings exits 0 on compliant payload.

    Payload must have visibility=public, default_branch=main, name=clinic-loop,
    Pages build_type=legacy with source_branch=gh-pages.
    """
    payload_path = FIXTURES_DIR / "compliant_repo.json"
    exit_code = check_settings(str(payload_path))
    assert exit_code == 0, f"Expected exit code 0, got {exit_code}"


def test_exit_one_lists_each_departing_field() -> None:
    """AC2: check_settings exits 1 and prints departing fields.

    When visibility is private and build_type is not legacy, output must contain
    lines for both visibility and build_type with expected and observed values.
    """
    payload_path = FIXTURES_DIR / "noncompliant_repo.json"

    # Capture stdout
    import io
    import contextlib

    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        exit_code = check_settings(str(payload_path))

    output_text = output.getvalue()

    assert exit_code == 1, f"Expected exit code 1, got {exit_code}"
    assert "visibility" in output_text, "Output must mention visibility field"
    assert "build_type" in output_text, "Output must mention build_type field"
    # Verify expected and observed values are mentioned
    assert "public" in output_text or "private" in output_text, "Output must show visibility values"
    assert "legacy" in output_text or "workflow" in output_text, "Output must show build_type values"


def test_missing_required_context_named_in_output() -> None:
    """AC3: Missing required status contexts are named in output.

    REQUIRED_STATUS_CONTEXTS must equal the six required names, and check_protection
    exits 1 naming each missing context.
    """
    from repo_settings.review_contexts import REQUIRED_STATUS_CONTEXTS

    expected = ("local-ci", "correctness", "security-privacy", "regulatory-guard", "test-quality", "docs")
    assert REQUIRED_STATUS_CONTEXTS == expected, f"Expected {expected}, got {REQUIRED_STATUS_CONTEXTS}"

    payload_path = FIXTURES_DIR / "noncompliant_protection.json"

    import io
    import contextlib

    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        exit_code = check_protection(str(payload_path))

    output_text = output.getvalue()

    assert exit_code == 1, f"Expected exit code 1, got {exit_code}"
    # Check that missing contexts are mentioned
    # The payload has only local-ci and correctness, so missing are:
    # security-privacy, regulatory-guard, test-quality, docs
    assert "security-privacy" in output_text, "Output must name missing security-privacy context"
    assert "regulatory-guard" in output_text, "Output must name missing regulatory-guard context"
    assert "test-quality" in output_text, "Output must name missing test-quality context"
    assert "docs" in output_text, "Output must name missing docs context"


def test_no_socket_is_opened_during_a_check() -> None:
    """AC5: Checkers don't open sockets, proving payloads are read from file/stdin only.

    With socket.socket monkeypatched to raise RuntimeError, checkers must return
    the same exit code as normal.
    """
    payload_path = FIXTURES_DIR / "compliant_repo.json"

    # Get the normal exit code
    normal_exit = check_settings(str(payload_path))

    # Now monkeypatch socket and verify same exit code
    with mock.patch("socket.socket", side_effect=RuntimeError("Socket access blocked")):
        monkeypatched_exit = check_settings(str(payload_path))

    assert monkeypatched_exit == normal_exit, (
        f"Exit code changed when socket blocked: normal={normal_exit}, monkeypatched={monkeypatched_exit}"
    )

    # Test check_protection as well
    protection_path = FIXTURES_DIR / "compliant_protection.json"
    normal_exit_prot = check_protection(str(protection_path))

    with mock.patch("socket.socket", side_effect=RuntimeError("Socket access blocked")):
        monkeypatched_exit_prot = check_protection(str(protection_path))

    assert monkeypatched_exit_prot == normal_exit_prot, (
        f"Protection exit code changed when socket blocked: normal={normal_exit_prot}, monkeypatched={monkeypatched_exit_prot}"
    )
