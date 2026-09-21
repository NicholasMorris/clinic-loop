"""World snapshot serialization and deserialization."""

from pathlib import Path

from .build import World


def write_world_snapshot(
    world: World,
    path: Path | str,
) -> None:
    """Serialize a world to JSON.

    Args:
        world: The World to serialize.
        path: Path to write the JSON file.

    Raises:
        NotImplementedError: This stub must be implemented.
    """
    raise NotImplementedError("write_world_snapshot stub")


def read_world_snapshot(path: Path | str) -> World:
    """Deserialize a world from JSON.

    Args:
        path: Path to read the JSON file.

    Returns:
        The deserialized World.

    Raises:
        NotImplementedError: This stub must be implemented.
    """
    raise NotImplementedError("read_world_snapshot stub")
