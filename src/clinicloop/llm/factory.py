"""Factory for building chat models from configuration."""

from langchain_openai import ChatOpenAI

from clinicloop.llm.config import MissingModelRole, get_models_config  # noqa: F401
from clinicloop.llm.fake import FakeChatModel


class UnknownModelRole(Exception):
    """Raised when requesting an unknown model role."""

    pass


__all__ = ["build_chat_model", "MissingModelRole", "UnknownModelRole"]


def build_chat_model(role: str) -> ChatOpenAI | FakeChatModel:
    """Build a ChatOpenAI model for the given role.

    Args:
        role: The model role (primary, judge, fallback, fake).

    Returns:
        A configured ChatOpenAI instance or FakeChatModel.

    Raises:
        UnknownModelRole: If the role is not recognized.
    """
    config = get_models_config()

    # Validate role
    valid_roles = {"primary", "judge", "fallback", "fake"}
    if role not in valid_roles:
        raise UnknownModelRole(f"Unknown model role: {role}")

    # Handle fake model specially
    if role == "fake":
        return FakeChatModel()

    # Get the row for this role
    row = getattr(config, role)

    # Build ChatOpenAI from the server row
    # Note: LM Studio doesn't require authentication
    model: ChatOpenAI | FakeChatModel = ChatOpenAI(
        model=row.repo_id,
        api_key="not-used",  # type: ignore  # LM Studio doesn't require auth
        base_url=row.base_url,
        temperature=row.temperature,
    )

    return model
