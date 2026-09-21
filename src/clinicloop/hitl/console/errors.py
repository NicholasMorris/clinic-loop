"""Exception types for the console package."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ConsoleSourceError:
    """An error reading from a console data source.

    Attributes:
        agent: The agent name where the error occurred.
        message: The error message.
    """

    agent: str
    message: str


class UnknownDecisionKind(ValueError):
    """Raised when an unknown decision kind is provided."""

    pass


class DecisionAlreadyRecorded(Exception):
    """Raised when a decision is already recorded for an item."""

    pass
