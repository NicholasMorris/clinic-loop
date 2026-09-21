"""Fake in-process chat model for testing."""

from langchain_core.messages import AIMessage, BaseMessage


class FakeChatModel:
    """In-process fake chat model that replays scripted responses.

    This model opens no network connections and is suitable for testing
    agent logic offline.
    """

    def __init__(self) -> None:
        """Initialize the fake model."""
        self._responses: list[str] = []
        self._index: int = 0

    def set_responses(self, responses: list[str]) -> None:
        """Set the scripted responses to replay.

        Args:
            responses: List of response strings to return in order.
        """
        self._responses = responses
        self._index = 0

    def invoke(self, prompt: str) -> BaseMessage:
        """Invoke the model with a prompt.

        Args:
            prompt: The input prompt.

        Returns:
            An AIMessage with the next scripted response.
        """
        if self._index >= len(self._responses):
            raise IndexError("No more scripted responses available")

        response = self._responses[self._index]
        self._index += 1

        return AIMessage(content=response)
