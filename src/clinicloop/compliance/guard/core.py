"""Guard core: pure function check for compliance rules."""

from .verdict import GuardVerdict


def check(thread: list, jurisdiction: str, ruleset, second_opinion=None) -> GuardVerdict:  # type: ignore[no-untyped-def]
    """Check a conversation thread against compliance rules.

    This is a pure function that performs no IO and never mutates its inputs.

    Args:
        thread: List of messages with 'role' and 'text' attributes/keys.
        jurisdiction: Jurisdiction code (e.g., 'au').
        ruleset: Ruleset object with jurisdiction, version, and rules.
        second_opinion: Optional callable that returns list of extra rule ids.

    Returns:
        GuardVerdict with allowed status and rule ids.

    Raises:
        ValueError: If thread has no assistant messages.
        JurisdictionMismatch: If ruleset.jurisdiction != jurisdiction.
    """
    raise NotImplementedError("check() stub")
