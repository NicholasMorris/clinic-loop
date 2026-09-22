"""Regulatory guard node: check draft against rules before human approval."""

from clinicloop.compliance.guard.core import check


def regulatory_guard(state: dict, ruleset) -> dict:  # type: ignore[no-untyped-def]
    """Run guard check on thread + draft.

    Args:
        state: Current TriageState as dict.
        ruleset: Ruleset object with jurisdiction, version, and rules.

    Returns:
        State update dict with guard_verdicts (and possibly routing_reason and routing_rule_ids).
    """
    # Build thread with draft as final assistant message
    redacted_thread = state.get("redacted_thread", [])
    draft_text = state.get("draft", "")

    # Convert to dict format
    thread_dicts = [{"role": turn.role, "text": turn.text} for turn in redacted_thread]

    # Add draft as assistant message if present
    if draft_text:
        thread_dicts.append({"role": "assistant", "text": draft_text})

    # Run guard check
    verdict = check(thread_dicts, ruleset.jurisdiction, ruleset)

    # Update guard verdicts list
    guard_verdicts = state.get("guard_verdicts", [])
    if not isinstance(guard_verdicts, list):
        guard_verdicts = [guard_verdicts]

    # Convert verdict to dict for serialization
    verdict_dict = {
        "allowed": verdict.allowed,
        "rule_ids": verdict.rule_ids,
        "jurisdiction": verdict.jurisdiction,
        "ruleset_version": verdict.ruleset_version,
        "text_sha256": verdict.text_sha256,
    }
    guard_verdicts.append(verdict_dict)

    update: dict[str, object] = {"guard_verdicts": guard_verdicts}

    # If blocked, set routing
    if not verdict.allowed:
        update["routing_reason"] = "rule_block"
        update["routing_rule_ids"] = tuple(verdict.rule_ids)

    return update
