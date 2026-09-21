"""Discrete-event simulation engine for SimClinic."""

from typing import Any


class Engine:
    """Heap-based discrete-event simulation engine.

    The engine advances a simulated clock only through scheduled events,
    maintaining four named queues and worker pools with service-time distributions.
    """

    def __init__(self, world: Any, regime_key: str = "au") -> None:
        """Initialize the engine.

        Args:
            world: The World object with generated entities.
            regime_key: Jurisdiction key ("au", "nz", or "uk").
        """
        self.world = world
        self.regime_key = regime_key

    def run(self, duration_minutes: int) -> None:
        """Run the simulation for the specified duration.

        Args:
            duration_minutes: Simulated duration in minutes.

        Raises:
            NotImplementedError: Stub implementation.
        """
        raise NotImplementedError("Engine.run")

    def run_hash(self) -> str:
        """Return a hash representing the run's event log.

        Returns:
            A string hash that uniquely identifies the run's events and outcomes.

        Raises:
            NotImplementedError: Stub implementation.
        """
        raise NotImplementedError("Engine.run_hash")
