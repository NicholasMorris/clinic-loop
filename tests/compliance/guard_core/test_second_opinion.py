"""Test second opinion mechanism.

AC6: The LLM second opinion is off by default in au.yaml and can only
add rule ids when enabled: with a stub reviewer returning allow for a
thread the deterministic rules block, the combined verdict is allowed=False
and retains the deterministic rule id; with the reviewer returning an extra
rule id on a blocked thread, verdict.rule_ids contains both ids.
"""

import dataclasses

from clinicloop.compliance.guard import check
from clinicloop.compliance.rulesets import load_ruleset


def test_llm_second_opinion_defaults_off_and_can_only_add_blocks() -> None:
    """Test second opinion is off by default and can only add rule ids."""
    ruleset = load_ruleset("au")

    # Thread that is blocked by deterministic rule
    blocked_thread = [
        {"role": "patient", "text": "Help me"},
        {"role": "assistant", "text": "Take veltrazine."},
    ]

    # 1. With second opinion OFF (default), reviewer is NEVER called
    reviewer_called = False

    def reviewer_that_raises(thread):  # type: ignore[no-untyped-def]
        nonlocal reviewer_called
        reviewer_called = True
        raise AssertionError("Reviewer should not be called when second_opinion_enabled=False")

    # Verify second_opinion_enabled is False by default
    assert not ruleset.second_opinion_enabled, (
        "Default ruleset must have second_opinion_enabled=False"
    )

    # Call check with second opinion disabled
    verdict_disabled = check(blocked_thread, "au", ruleset, second_opinion=reviewer_that_raises)

    assert not reviewer_called, "Reviewer was called when second_opinion_enabled=False"
    assert not verdict_disabled.allowed, "Deterministic rule should block"
    assert "AU-G-PRODUCT" in verdict_disabled.rule_ids

    # 2. With second opinion enabled, reviewer CAN add rule ids
    ruleset_with_opinion = dataclasses.replace(
        ruleset, second_opinion_enabled=True
    )

    # Case 2a: Reviewer returns [] on blocked thread (no extra rules)
    # Result: stays blocked with deterministic id
    def reviewer_no_extras(thread):  # type: ignore[no-untyped-def]
        return []

    verdict_no_extras = check(
        blocked_thread, "au", ruleset_with_opinion, second_opinion=reviewer_no_extras
    )
    assert not verdict_no_extras.allowed, "Blocked thread stays blocked with empty review"
    assert "AU-G-PRODUCT" in verdict_no_extras.rule_ids

    # Case 2b: Reviewer returns extra rule id on blocked thread
    # Result: verdict includes both deterministic id and reviewer id
    def reviewer_with_extra(thread):  # type: ignore[no-untyped-def]
        return ["X-EXTRA"]

    verdict_with_extra = check(
        blocked_thread, "au", ruleset_with_opinion, second_opinion=reviewer_with_extra
    )
    assert not verdict_with_extra.allowed, "Blocked thread stays blocked"
    assert "AU-G-PRODUCT" in verdict_with_extra.rule_ids
    assert "X-EXTRA" in verdict_with_extra.rule_ids

    # Case 2c: Reviewer adds rule id to clean thread
    # Result: verdict becomes blocked with reviewer's id
    clean_thread = [
        {"role": "patient", "text": "Help me"},
        {"role": "assistant", "text": "I can help you."},
    ]

    verdict_clean = check(
        clean_thread, "au", ruleset_with_opinion, second_opinion=reviewer_with_extra
    )
    assert not verdict_clean.allowed, "Reviewer added block"
    assert "X-EXTRA" in verdict_clean.rule_ids
    assert "AU-G-PRODUCT" not in verdict_clean.rule_ids
