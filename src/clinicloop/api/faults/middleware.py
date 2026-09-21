"""Fault injection middleware for FastAPI."""

from typing import Callable

from fastapi import FastAPI, Request, Response


class FaultLog(dict):
    """Entry in the fault log.

    Inherits from dict to allow JSON serialization.
    """

    pass


class FaultMiddleware:
    """Middleware for injecting faults into API responses.

    Faults are deterministic based on a seeded random number generator,
    allowing reproducible fault sequences for testing.
    """

    def __init__(
        self,
        app: FastAPI,
        profile: "FaultProfile",  # noqa: F821
        sleep_fn: Callable[[float], None] | None = None,
    ) -> None:
        """Initialize the fault injection middleware.

        Args:
            app: The FastAPI application instance.
            profile: The fault profile configuration.
            sleep_fn: Optional callable to simulate delay (for testing).
                If not provided, real time.sleep is used.
        """
        self.app = app
        self.profile = profile
        self.sleep_fn = sleep_fn or __import__("time").sleep
        self.fault_log: list[FaultLog] = []

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Dispatch the request through fault injection.

        Args:
            request: The incoming HTTP request.
            call_next: The next middleware or route handler.

        Returns:
            The response, possibly modified with injected faults.

        Raises:
            NotImplementedError: Stub implementation.
        """
        raise NotImplementedError("FaultMiddleware.dispatch stub")

    def get_fault_log(self) -> list[dict]:
        """Get the current fault log.

        Returns:
            List of fault log entries.
        """
        return self.fault_log


def attach_fault_middleware(
    app: FastAPI,
    profile: "FaultProfile",  # noqa: F821
    sleep_fn: Callable[[float], None] | None = None,
) -> FaultMiddleware:
    """Attach the fault injection middleware to a FastAPI app.

    Args:
        app: The FastAPI application instance.
        profile: The fault profile configuration.
        sleep_fn: Optional callable to simulate delay (for testing).

    Returns:
        The FaultMiddleware instance.
    """
    middleware = FaultMiddleware(app, profile, sleep_fn)
    app.add_middleware(lambda app: middleware)
    return middleware
