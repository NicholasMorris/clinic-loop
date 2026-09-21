"""SLA rules for SimClinic."""


def sla_rules() -> dict[str, str]:
    """Return the mapping of SLA rule IDs to inventory IDs.

    Returns:
        A dictionary mapping rule IDs to their cited inventory IDs.
        Keys: "termination_cutoff", "damage_report_window", "dispatch_commitment".
    """
    return {
        "termination_cutoff": "ps-03",
        "damage_report_window": "ps-04",
        "dispatch_commitment": "po-01",
    }
