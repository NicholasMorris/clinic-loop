"""WorldMessageSource: adapts the SimClinic world to the MessageSource protocol."""

from typing import Any


class WorldMessageSource:
    """Implements MessageSource by looking up messages in a SimClinic world.

    Attributes:
        world: The SimClinic world object with a messages list.
    """

    def __init__(self, world: Any) -> None:
        """Initialize with a world.

        Args:
            world: The SimClinic world with entities.messages.
        """
        self.world = world

    def fetch(self, message_id: str) -> str:
        """Fetch the raw message text for the given message_id.

        Args:
            message_id: Unique message identifier.

        Returns:
            The raw unredacted message text.

        Raises:
            KeyError: If the message_id is not found in the world.
        """
        for message in self.world.messages:
            if message.message_id == message_id:
                return str(message.body)
        raise KeyError(f"Message {message_id} not found in world")
