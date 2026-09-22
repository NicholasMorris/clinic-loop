"""Regulatory guard node: check draft against rules before human approval."""


def regulatory_guard(state: dict, ruleset) -> dict:  # type: ignore[no-untyped-def]
    """Run guard check on thread + draft.

    Args:
        state: Current TriageState as dict.
        ruleset: Ruleset object with jurisdiction, version, and rules.

    Returns:
        State update dict with guard_verdicts (and possibly routing_reason and routing_rule_ids).

    Raises:
        NotImplementedError: Until implemented.
    """
    raise NotImplementedError("regulatory_guard not yet implemented")
