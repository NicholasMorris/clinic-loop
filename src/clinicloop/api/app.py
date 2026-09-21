"""FastAPI application factory for SimClinic mock APIs."""

from pathlib import Path

from fastapi import FastAPI


class SnapshotVersionUnsupported(Exception):
    """Raised when snapshot schema version is not supported."""

    pass


def create_app(snapshot_path: Path | str, host: str = "127.0.0.1") -> FastAPI:
    """Create and configure the FastAPI application.

    Loads a world snapshot from the given path and configures the FastAPI
    app with routes for patients, orders, consults, and messages.

    Args:
        snapshot_path: Path to the world snapshot JSON file.
        host: Host to bind to (must be loopback: 127.0.0.1, ::1, or localhost).

    Returns:
        A configured FastAPI application.

    Raises:
        SnapshotVersionUnsupported: If snapshot schema_version is not "1".
        ValueError: If host is not a loopback address.
        NotImplementedError: Stub implementation.
    """
    raise NotImplementedError("create_app is not yet implemented")
