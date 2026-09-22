"""MessageSource protocol for injecting patient messages into the graph."""

from typing import Protocol


class MessageSource(Protocol):
    """Protocol for retrieving raw patient messages by ID.

    This allows the graph to bind a closure that holds the raw message and
    returns only opaque message_id through config, avoiding PII leakage to
    the checkpoint db.
    """

    def fetch(self, message_id: str) -> str:
        """Fetch the raw message text for the given message_id.

        Args:
            message_id: Unique message identifier (opaque, not PII).

        Returns:
            The raw unredacted message text.
        """
        ...


class InMemoryMessageSource:
    """In-memory implementation of MessageSource for testing.

    Attributes:
        messages: Dict mapping message_id to raw message text.
    """

    def __init__(self, messages: dict[str, str]) -> None:
        """Initialize with a dict of messages.

        Args:
            messages: Mapping of message_id to raw text.
        """
        self.messages = messages

    def fetch(self, message_id: str) -> str:
        """Fetch a message by ID.

        Args:
            message_id: The message identifier.

        Returns:
            The raw message text.

        Raises:
            KeyError: If message_id is not found.
        """
        return self.messages[message_id]
