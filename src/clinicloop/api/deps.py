"""Dependency injection utilities for FastAPI."""

from typing import Callable

from clinicloop.world.generator.build import World


def get_world_factory(world: World) -> Callable[[], World]:
    """Create a factory function for world dependency injection.

    Args:
        world: The world instance to inject.

    Returns:
        A callable that returns the world.
    """

    def _get_world() -> World:
        return world

    return _get_world
