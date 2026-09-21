"""FastAPI application factory for SimClinic mock APIs."""

from pathlib import Path

from fastapi import FastAPI

from clinicloop.world.generator.build import World
from clinicloop.world.generator.snapshot import read_world_snapshot

from .guard_boundary import register_guard_handler
from .routes import consults, messages, orders, patients


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
    """
    # Validate host is loopback only
    loopback_hosts = {"127.0.0.1", "::1", "localhost"}
    if host not in loopback_hosts:
        raise ValueError(f"Host must be loopback (127.0.0.1, ::1, or localhost), got {host}")

    # Load and validate snapshot
    try:
        world = read_world_snapshot(snapshot_path)
    except ValueError as e:
        if "Unsupported schema version" in str(e):
            raise SnapshotVersionUnsupported(
                f"Snapshot schema version unsupported. Expected: 1, Got: {e}"
            ) from e
        raise

    # Create app
    app = FastAPI(
        title="SimClinic Mock APIs",
        description="Mock APIs for SimClinic world snapshot",
        version="1.0.0",
    )

    # Initialize app state for message storage
    # Message counter starts after the highest existing message ID
    app.state.created_messages = {}
    if world.messages:
        # Extract numbers from message IDs like "M000001" and find the maximum
        max_id = max(int(m.message_id[1:]) for m in world.messages)
        app.state.message_counter = max_id
    else:
        app.state.message_counter = 0

    # Create a function to be used as a dependency
    def get_world_impl() -> World:
        """Return the loaded world snapshot.

        Returns:
            The World instance.
        """
        return world

    # Register guard exception handler
    register_guard_handler(app)

    # Register routes
    app.include_router(patients.router)
    app.include_router(orders.router)
    app.include_router(consults.router)
    app.include_router(messages.router)

    # Override the specific get_world dependencies from each route module
    app.dependency_overrides[patients.get_world] = get_world_impl
    app.dependency_overrides[orders.get_world] = get_world_impl
    app.dependency_overrides[consults.get_world] = get_world_impl
    app.dependency_overrides[messages.get_world] = get_world_impl

    return app
