"""Fixtures for guard boundary tests."""

from pathlib import Path
from typing import Any, Callable

import pytest
from fastapi import Request
from fastapi.testclient import TestClient
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from clinicloop.api.app import create_app
from clinicloop.world.generator.build import generate_world
from clinicloop.world.generator.snapshot import write_world_snapshot


@pytest.fixture
def world_snapshot(tmp_path: Path) -> Path:
    """Generate a test world snapshot in a temporary directory.

    Args:
        tmp_path: Temporary directory fixture from pytest.

    Returns:
        Path to the written snapshot file.
    """
    world = generate_world(seed=42, population_size=10, span_days=30)
    snapshot_path = tmp_path / "test_snapshot.json"
    write_world_snapshot(world, snapshot_path)
    return snapshot_path


@pytest.fixture
def app(world_snapshot: Path) -> Any:
    """Create a FastAPI app with a loaded snapshot.

    Args:
        world_snapshot: Path to the snapshot file.

    Returns:
        A FastAPI application instance.
    """
    return create_app(snapshot_path=world_snapshot)


@pytest.fixture
def client(app: Any) -> TestClient:
    """Create a FastAPI test client.

    Args:
        app: The FastAPI application instance.

    Returns:
        A TestClient for the app.
    """
    return TestClient(app)


class FaultInjectingMiddleware(BaseHTTPMiddleware):
    """ASGI middleware that injects faults on /messages POST.

    Modes:
    - 'latency': Add 50ms delay before passing request through.
    - 'http_500': After guard runs, inject a 500 response.
    - 'http_429': After guard runs, inject a 429 response.
    """

    def __init__(self, app: Any, mode: str, call_order: list[str]) -> None:
        """Initialize the middleware.

        Args:
            app: The ASGI app.
            mode: One of 'latency', 'http_500', 'http_429'.
            call_order: Shared list to record call order.
        """
        super().__init__(app)
        self.mode = mode
        self.call_order = call_order

    async def dispatch(self, request: Request, call_next: Callable[..., Any]) -> Response:
        """Process request and inject faults on POST /messages only.

        Args:
            request: The request.
            call_next: The next middleware/handler.

        Returns:
            The response, possibly with injected fault.
        """
        import asyncio

        # Only inject faults on POST /messages
        if request.method != "POST" or request.url.path != "/messages":
            return await call_next(request)  # type: ignore[no-any-return]

        if self.mode == "latency":
            # Add latency and let the real response through
            await asyncio.sleep(0.05)
            return await call_next(request)  # type: ignore[no-any-return]

        if self.mode in ("http_500", "http_429"):
            # Let the guard run first (so it records in app.state.guard_trace)
            await call_next(request)

            # Record the fault injection
            fault_name = "http_500" if self.mode == "http_500" else "http_429"
            self.call_order.append(fault_name)

            # Return the injected status
            from starlette.responses import JSONResponse

            status_code = 500 if self.mode == "http_500" else 429
            return JSONResponse(
                {"detail": f"Fault injected: {fault_name}"}, status_code=status_code
            )

        # No fault
        return await call_next(request)  # type: ignore[no-any-return]


@pytest.fixture
def fault_app(app: Any) -> tuple[Any, list[str]]:
    """Create an app with fault injection middleware and a call_order list.

    The call_order list is shared with the app state so that guard runs are recorded.

    Args:
        app: The FastAPI application instance.

    Returns:
        Tuple of (app, call_order list).
    """
    call_order: list[str] = []
    app.state.guard_trace = call_order

    return app, call_order


@pytest.fixture
def fault_client_factory(fault_app: tuple[Any, list[str]]) -> Any:
    """Create a factory for fault clients with different modes.

    Args:
        fault_app: Tuple of (app, call_order list).

    Returns:
        A function that creates a client with a specific fault mode.
    """
    app, call_order = fault_app

    def make_client(mode: str) -> tuple[TestClient, list[str]]:
        """Create a client with the specified fault mode.

        Args:
            mode: The fault mode ('latency', 'http_500', or 'http_429').

        Returns:
            Tuple of (TestClient, call_order list).
        """
        # Reset the call_order for this client
        call_order.clear()
        app.state.guard_trace = call_order

        # Add the middleware
        app.add_middleware(FaultInjectingMiddleware, mode=mode, call_order=call_order)

        return TestClient(app), call_order

    return make_client
