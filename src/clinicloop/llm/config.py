"""Configuration loader for models.toml."""

from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


# Exception classes
class NonLoopbackBaseURL(Exception):
    """Raised when a server row has a non-loopback base_url."""

    pass


class MissingModelRole(Exception):
    """Raised when a required model role is missing."""

    pass


class UnknownModelRole(Exception):
    """Raised when requesting an unknown model role."""

    pass


class FakeRowHasServerFields(Exception):
    """Raised when a fake row contains server-only fields."""

    pass


class ServerModelRow(BaseModel):
    """Configuration for a server-based model."""

    kind: Literal["server"]
    repo_id: str
    revision: str
    quant: str
    family: str
    base_url: str
    structured_method: Literal["tools", "json_schema"]
    parallel_tool_calls: bool
    reasoning_handling: str
    context_window: int
    temperature: float
    seed: int

    @field_validator("revision")
    @classmethod
    def validate_revision_not_main(cls, v: str) -> str:
        """Revision must be a pinned commit SHA, not 'main'."""
        if v == "main":
            raise ValueError("revision cannot be 'main'; must be a pinned commit SHA")
        return v

    @field_validator("quant")
    @classmethod
    def validate_quant_not_empty(cls, v: str) -> str:
        """Quant cannot be empty."""
        if not v:
            raise ValueError("quant cannot be empty")
        return v


class FakeModelRow(BaseModel):
    """Configuration for the fake in-process model."""

    kind: Literal["fake"]
    family: str
    structured_method: Literal["tools", "json_schema"]
    temperature: float
    seed: int

    @field_validator("*", mode="before")
    @classmethod
    def check_no_server_fields(cls, v: Any, info: Any) -> Any:
        """Fake rows must not contain server-only fields."""
        raise NotImplementedError


class ModelsConfig(BaseModel):
    """Complete models configuration."""

    primary: ServerModelRow
    judge: ServerModelRow
    fallback: ServerModelRow
    fake: FakeModelRow


# Module-level storage for loaded config
_loaded_config: ModelsConfig | None = None


def load_models_config(config_path: Path) -> ModelsConfig:
    """Load and validate models.toml.

    Args:
        config_path: Path to models.toml file.

    Returns:
        Parsed configuration.

    Raises:
        MissingModelRole: If a required role is missing.
        NonLoopbackBaseURL: If a server row has a non-loopback base_url.
        FakeRowHasServerFields: If a fake row contains server-only fields.
        ValidationError: If validation fails.
    """
    raise NotImplementedError
