"""Factory for building chat models from configuration."""

from langchain_openai import ChatOpenAI

from clinicloop.llm.config import ServerModelRow


class MissingModelRole(Exception):
    """Raised when a required model role is missing."""

    pass


class UnknownModelRole(Exception):
    """Raised when requesting an unknown model role."""

    pass


def build_chat_model(role: str) -> ChatOpenAI:
    """Build a ChatOpenAI model for the given role.

    Args:
        role: The model role (primary, judge, fallback, fake).

    Returns:
        A configured ChatOpenAI instance.

    Raises:
        UnknownModelRole: If the role is not recognized.
    """
    raise NotImplementedError
