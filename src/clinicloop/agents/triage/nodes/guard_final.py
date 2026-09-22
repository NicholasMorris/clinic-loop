"""Guard final node: re-check post-edit text after human approval."""

from typing import Any

from clinicloop.compliance.guard.core import check


def guard_final(state: dict[str, Any], ruleset) -> dict[str, Any]:  # type: ignore[no-untyped-def]
    """Re-check the exact post-edit text from human_decision.

    Args:
        state: Current TriageState as dict (must have human_decision).
        ruleset: Ruleset object with jurisdiction, version, and rules.

    Returns:
        State update dict with final guard_verdict (and possibly routing_reason
        and routing_rule_ids).

    Raises:
        ValueError: If human_decision is None.
    """
    human_decision = state.get("human_decision")
    if human_decision is None:
        raise ValueError("guard_final requires a human_decision")

    # Determine which text to check
    if human_decision.action == "edit" and human_decision.edited_text:
        final_text = human_decision.edited_text
    else:
        # Approve or reject: use the draft
        final_text = state.get("draft", "")

    # Build thread with final text as assistant message
    redacted_thread = state.get("redacted_thread", [])
    thread_dicts = [{"role": turn.role, "text": turn.text} for turn in redacted_thread]

    if final_text:
        thread_dicts.append({"role": "assistant", "text": final_text})

    # Run final guard check
    verdict = check(thread_dicts, ruleset.jurisdiction, ruleset)

    # Update guard verdicts list
    guard_verdicts = state.get("guard_verdicts", [])
    if not isinstance(guard_verdicts, list):
        guard_verdicts = [guard_verdicts]

    guard_verdicts.append(verdict)

    update: dict[str, object] = {"guard_verdicts": guard_verdicts}

    # If blocked, set routing
    if not verdict.allowed:
        update["routing_reason"] = "rule_block"
        update["routing_rule_ids"] = tuple(verdict.rule_ids)

    return update
