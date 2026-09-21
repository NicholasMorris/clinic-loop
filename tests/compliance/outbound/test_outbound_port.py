"""Test OutboundPort send() validation.

AC3: OutboundPort.send raises GuardMismatch when sha256(text) differs
from verdict.text_sha256, GuardBlocked when verdict.allowed is False,
and StaleRuleset when the loaded ruleset version differs from verdict.ruleset_version;
only a matching allowed verdict at the current version reaches the transport stub,
which records exactly one call.
"""

import hashlib

from clinicloop.compliance.guard.verdict import GuardVerdict
from clinicloop.compliance.outbound import (
    GuardBlocked,
    GuardMismatch,
    OutboundPort,
    StaleRuleset,
)
from clinicloop.compliance.rulesets import load_ruleset


def test_send_rejects_mismatched_blocked_and_stale_verdicts() -> None:
    """Test OutboundPort.send raises appropriate errors."""
    ruleset = load_ruleset("au")

    # Create a transport stub that records calls
    transport_calls = []

    def transport(text: str) -> None:
        transport_calls.append(text)

    port = OutboundPort(transport, ruleset)

    # Test 1: GuardMismatch when sha256 doesn't match
    text = "Hello world"
    wrong_sha = "0000000000000000000000000000000000000000000000000000000000000000"
    verdict_mismatch = GuardVerdict(
        allowed=True,
        rule_ids=(),
        jurisdiction="au",
        ruleset_version=ruleset.version,
        text_sha256=wrong_sha,
    )

    import pytest

    with pytest.raises(GuardMismatch):
        port.send(text, verdict_mismatch)
    assert len(transport_calls) == 0, "Transport called on mismatch"

    # Test 2: GuardBlocked when verdict.allowed is False
    correct_sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
    verdict_blocked = GuardVerdict(
        allowed=False,
        rule_ids=("AU-G-PRODUCT",),
        jurisdiction="au",
        ruleset_version=ruleset.version,
        text_sha256=correct_sha,
    )

    with pytest.raises(GuardBlocked):
        port.send(text, verdict_blocked)
    assert len(transport_calls) == 0, "Transport called on block"

    # Test 3: StaleRuleset when verdict.ruleset_version differs
    verdict_stale = GuardVerdict(
        allowed=True,
        rule_ids=(),
        jurisdiction="au",
        ruleset_version="2026-01-01.0",  # Different from current
        text_sha256=correct_sha,
    )

    with pytest.raises(StaleRuleset):
        port.send(text, verdict_stale)
    assert len(transport_calls) == 0, "Transport called on stale"

    # Test 4: Allowed verdict at current version reaches transport
    verdict_ok = GuardVerdict(
        allowed=True,
        rule_ids=(),
        jurisdiction="au",
        ruleset_version=ruleset.version,
        text_sha256=correct_sha,
    )

    port.send(text, verdict_ok)
    assert len(transport_calls) == 1, "Transport not called"
    assert transport_calls[0] == text, "Wrong text sent"
