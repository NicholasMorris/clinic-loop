"""Structured output handling with fallback."""

from typing import Any, Type, TypeVar

from langchain_openai import ChatOpenAI
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

# Global tracking of structured output method used
structured_method_used: str = ""


def structured_output(
    model: ChatOpenAI, schema: Type[T], prompt: str
) -> T:
    """Get structured output from a model with fallback.

    Attempts to extract structured output using the model's configured method.
    If tool calling fails, falls back to JSON schema exactly once.

    Args:
        model: The chat model.
        schema: The Pydantic schema to extract.
        prompt: The prompt to send to the model.

    Returns:
        An instance of the schema.

    Sets:
        structured_method_used: The method that succeeded ("tools" or "json_schema").
    """
    raise NotImplementedError
