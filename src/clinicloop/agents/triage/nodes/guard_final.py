"""Guard final node: re-check post-edit text after human approval."""


def guard_final(state: dict, ruleset) -> dict:  # type: ignore[no-untyped-def]
    """Re-check the exact post-edit text from human_decision.

    Args:
        state: Current TriageState as dict (must have human_decision).
        ruleset: Ruleset object with jurisdiction, version, and rules.

    Returns:
        State update dict with final guard_verdict (and possibly routing_reason and routing_rule_ids).

    Raises:
        NotImplementedError: Until implemented.
        ValueError: If human_decision is None.
    """
    raise NotImplementedError("guard_final not yet implemented")
