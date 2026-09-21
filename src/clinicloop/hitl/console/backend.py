"""Backend for the review console."""

from dataclasses import dataclass
from typing import Any, Sequence

from clinicloop.hitl.console.errors import (
    ConsoleSourceError,
    DecisionAlreadyRecorded,
    UnknownDecisionKind,
)


@dataclass(frozen=True)
class PendingItem:
    """A pending item awaiting human decision.

    Attributes:
        agent: The agent name.
        case_id: The case identifier.
        node: The interrupted node name.
        payload: The state payload dict.
        interrupted_at: ISO string timestamp of interruption.
    """

    agent: str
    case_id: str
    node: str
    payload: dict[str, Any]
    interrupted_at: str


@dataclass(frozen=True)
class PendingListing:
    """A listing of pending items and any errors.

    Attributes:
        items: List of pending items.
        errors: List of source errors encountered.
    """

    items: list[PendingItem]
    errors: list[ConsoleSourceError]


def list_pending(agents: Sequence[str] | None = None) -> PendingListing:
    """List pending items from checkpoint databases.

    Args:
        agents: Sequence of agent names to query, or None to query all.

    Returns:
        A PendingListing with items and errors.

    Raises:
        NotImplementedError: Stub implementation.
    """
    raise NotImplementedError


def apply_decision(
    agent: str,
    case_id: str,
    kind: str,
    reviewer: str,
    *,
    edited_text: str | None = None,
    reason: str | None = None,
) -> dict[str, Any]:
    """Apply a human decision to a pending item.

    Args:
        agent: The agent name.
        case_id: The case identifier.
        kind: The decision kind ("approve", "edit", or "reject").
        reviewer: The reviewer identifier.
        edited_text: Optional edited text when kind is "edit".
        reason: Optional reason when kind is "reject".

    Returns:
        The recorded decision dict.

    Raises:
        UnknownDecisionKind: If kind is not one of the known values.
        DecisionAlreadyRecorded: If a decision is already recorded.
        NotImplementedError: Stub implementation.
    """
    raise NotImplementedError
