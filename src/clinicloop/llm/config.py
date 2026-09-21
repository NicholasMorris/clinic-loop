"""Configuration loader for models.toml."""

from pathlib import Path
from typing import Any, Literal
from urllib.parse import urlparse

import tomli
from pydantic import BaseModel, field_validator


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
    # Optional fields that should NOT be present
    repo_id: str | None = None
    revision: str | None = None
    quant: str | None = None
    base_url: str | None = None

    @field_validator("repo_id", "revision", "quant", "base_url", mode="after")
    @classmethod
    def check_no_server_fields(cls, v: Any, info: Any) -> Any:
        """Fake rows must not contain server-only fields."""
        if v is not None:
            field_name = info.field_name
            raise FakeRowHasServerFields(f"Fake row must not have field '{field_name}'")
        return v


class ModelsConfig(BaseModel):
    """Complete models configuration."""

    primary: ServerModelRow
    judge: ServerModelRow
    fallback: ServerModelRow
    fake: FakeModelRow


# Module-level storage for loaded config
_loaded_config: ModelsConfig | None = None


def _validate_loopback_url(url: str, role: str) -> None:
    """Validate that a base_url uses a loopback address.

    Args:
        url: The base URL to validate.
        role: The role name (for error messages).

    Raises:
        NonLoopbackBaseURL: If the URL doesn't use a loopback address.
    """
    parsed = urlparse(url)
    host = parsed.hostname or ""

    loopback_hosts = {"127.0.0.1", "::1", "localhost"}
    if host not in loopback_hosts:
        raise NonLoopbackBaseURL(f"Server row '{role}' has non-loopback base_url: {url}")


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
    global _loaded_config

    # Read TOML file
    with open(config_path, "rb") as f:
        data = tomli.load(f)

    # Check for required roles
    required_roles = {"primary", "judge", "fallback", "fake"}
    missing_roles = required_roles - set(data.keys())
    if missing_roles:
        missing_role = missing_roles.pop()
        raise MissingModelRole(f"Required role '{missing_role}' is missing")

    # Validate the configuration
    config = ModelsConfig(**data)

    # Validate loopback URLs for server rows
    for role_name in ["primary", "judge", "fallback"]:
        row = getattr(config, role_name)
        if row.kind == "server":
            _validate_loopback_url(row.base_url, role_name)

    # Store the config globally for factory access
    _loaded_config = config

    return config


def get_models_config() -> ModelsConfig:
    """Get the loaded models configuration.

    Returns:
        The previously loaded configuration.

    Raises:
        RuntimeError: If no configuration has been loaded.
    """
    if _loaded_config is None:
        raise RuntimeError("Models configuration not loaded. Call load_models_config first.")
    return _loaded_config
