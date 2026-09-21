"""Structured output handling with fallback."""

from typing import Any, Type, TypeVar, cast

from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from clinicloop.llm.config import get_models_config

T = TypeVar("T", bound=BaseModel)

# Global tracking of structured output method used
structured_method_used: str = ""


def structured_output(model: ChatOpenAI, schema: Type[T], prompt: str) -> T:
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
    global structured_method_used

    config = get_models_config()

    # Determine which method to use based on the model's configuration
    # We need to figure out which role this model is for
    # Try to match by model_name to the config
    model_role = None
    for role_name in ["primary", "judge", "fallback"]:
        row = getattr(config, role_name)
        if row.repo_id == model.model_name:
            model_role = role_name
            break

    if model_role is None:
        # Default to json_schema if we can't determine the role
        structured_method_used = "json_schema"
        structured_model = model.with_structured_output(schema, method="json_schema")
        result: Any = structured_model.invoke(prompt)
        return cast(T, result)

    row = getattr(config, model_role)
    primary_method = row.structured_method

    # Try the primary method first
    if primary_method == "tools":
        try:
            structured_model = model.with_structured_output(schema, method="function_calling")
            result = structured_model.invoke(prompt)
            structured_method_used = "tools"
            return cast(T, result)
        except Exception:
            # Fall back to json_schema
            structured_model = model.with_structured_output(schema, method="json_schema")
            result = structured_model.invoke(prompt)
            structured_method_used = "json_schema"
            return cast(T, result)
    else:  # json_schema
        structured_model = model.with_structured_output(schema, method="json_schema")
        result = structured_model.invoke(prompt)
        structured_method_used = "json_schema"
        return cast(T, result)
