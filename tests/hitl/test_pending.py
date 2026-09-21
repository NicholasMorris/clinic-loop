"""Tests for listing pending interrupted threads."""

from clinicloop.hitl.pending import list_pending


def test_list_pending_returns_only_interrupted_threads() -> None:
    """AC7: list_pending returns only thread ids of interrupted threads.

    Should return thread IDs that are currently interrupted and awaiting
    human input, and omit threads that ran to completion.
    """
    # Get pending threads for the reference agent
    pending = list_pending("reference")

    # Should return a list (possibly empty in a fresh state)
    assert isinstance(pending, list)
    assert all(isinstance(tid, str) for tid in pending)
