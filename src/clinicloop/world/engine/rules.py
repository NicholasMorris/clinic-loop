"""SLA rules for SimClinic."""


def sla_rules() -> dict[str, str]:
    """Return the mapping of SLA rule IDs to inventory IDs.

    Returns:
        A dictionary mapping rule IDs to their cited inventory IDs.
        Expected keys: "termination_cutoff", "damage_report_window", "dispatch_commitment".

    Raises:
        NotImplementedError: Stub implementation.
    """
    raise NotImplementedError("sla_rules")
