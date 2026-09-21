"""Fake in-process chat model for testing."""

from typing import Any

from langchain_core.messages import BaseMessage, AIMessage


class FakeChatModel:
    """In-process fake chat model that replays scripted responses.

    This model opens no network connections and is suitable for testing
    agent logic offline.
    """

    def __init__(self) -> None:
        """Initialize the fake model."""
        raise NotImplementedError

    def set_responses(self, responses: list[str]) -> None:
        """Set the scripted responses to replay.

        Args:
            responses: List of response strings to return in order.
        """
        raise NotImplementedError

    def invoke(self, prompt: str) -> BaseMessage:
        """Invoke the model with a prompt.

        Args:
            prompt: The input prompt.

        Returns:
            An AIMessage with the next scripted response.
        """
        raise NotImplementedError
