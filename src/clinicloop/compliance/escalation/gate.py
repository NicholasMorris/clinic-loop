"""Escalation gate for draft entry point."""

from typing import Callable, Optional, TypeVar

from clinicloop.compliance.escalation.result import EscalationClear, EscalationRequired

T = TypeVar("T")


def draft(
    thread: list[dict[str, str]],
    clear: Optional[EscalationClear],
    drafter: Callable[[list[dict[str, str]]], T],
) -> T:
    """Guard draft entry point with an escalation clear token.

    Raises EscalationRequired if clear is None or its text_sha256 does not match
    the thread hash. Otherwise calls drafter(thread) and returns the result.

    Args:
        thread: The message thread.
        clear: Optional EscalationClear token from detector.
        drafter: Callable that drafts a response.

    Returns:
        Result of drafter(thread).

    Raises:
        EscalationRequired: If clear is None or does not match thread.
        NotImplementedError: Stub.
    """
    raise NotImplementedError("draft() not yet implemented")
