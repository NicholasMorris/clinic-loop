"""Fault injection middleware for FastAPI."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any, Callable, Optional, cast

import numpy as np
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

if TYPE_CHECKING:
    from clinicloop.api.faults.profile import FaultProfile, RateLimitRule


class FaultLog(dict[str, Any]):
    """Entry in the fault log.

    Inherits from dict to allow JSON serialization.
    """

    pass


class FaultMiddlewareInstance:
    """Stateful instance of fault injection middleware."""

    def __init__(
        self,
        profile: FaultProfile,
        sleep_fn: Optional[Callable[[float], None]] = None,
    ) -> None:
        """Initialize the fault middleware instance.

        Args:
            profile: The fault profile configuration.
            sleep_fn: Optional callable to simulate delay (for testing).
                If not provided, real time.sleep is used.
        """
        self.profile = profile
        self.sleep_fn = sleep_fn or time.sleep
        self.fault_log: list[FaultLog] = []
        self.request_ordinal = 0

        # Initialize seeded RNG for reproducible faults
        self.rng = np.random.Generator(np.random.PCG64(profile.seed))

        # Track rate limiting per route: {route: [(timestamp, count), ...]}
        self.rate_limit_windows: dict[str, list[tuple[float, int]]] = {}

    def get_fault_log(self) -> list[FaultLog]:
        """Get the current fault log.

        Returns:
            List of fault log entries.
        """
        return self.fault_log

    def check_and_inject_fault(
        self, request: Request, call_next: Callable[..., Any]
    ) -> tuple[bool, Optional[Response]]:
        """Check for faults and return fault response if applicable.

        Args:
            request: The incoming HTTP request.
            call_next: The next handler.

        Returns:
            Tuple of (should_inject_fault, fault_response).
            If should_inject_fault is False, proceed normally.
            If True, use fault_response.
        """
        # Build route key from method and path
        route_key = f"{request.method} {request.url.path}"

        # Increment ordinal for this request
        self.request_ordinal += 1
        ordinal = self.request_ordinal

        # Check if this route has fault rules
        if route_key not in self.profile.routes:
            # No faults for this route
            return False, None

        route_rules = self.profile.routes[route_key]
        current_time = time.time()

        # Check rate limiting first
        if route_rules.rate_limit is not None:
            rate_limit_entry = self._check_rate_limit(
                route_key, route_rules.rate_limit, current_time
            )
            if rate_limit_entry is not None:
                # Rate limited - return 429
                self.fault_log.append(rate_limit_entry)
                response = Response(
                    content='{"fault_kind": "rate_limit"}',
                    status_code=429,
                    media_type="application/json",
                )
                response.headers["Retry-After"] = str(
                    rate_limit_entry.get("retry_after_seconds", 60)
                )
                return True, response

        # Check for server errors
        if route_rules.server_error is not None:
            error_prob = route_rules.server_error.probability
            if self.rng.random() < error_prob:
                # Inject error
                fault_entry = FaultLog(
                    ordinal=ordinal,
                    route=route_key,
                    fault_kind="server_error",
                )
                self.fault_log.append(fault_entry)
                status = route_rules.server_error.status
                response = Response(
                    content='{"fault_kind": "server_error"}',
                    status_code=status,
                    media_type="application/json",
                )
                return True, response

        # Check for latency injection
        if route_rules.latency is not None:
            latency_prob = route_rules.latency.probability
            if self.rng.random() < latency_prob:
                # Inject latency
                latency_ms = route_rules.latency.latency_ms
                latency_seconds = latency_ms / 1000.0
                fault_entry = FaultLog(
                    ordinal=ordinal,
                    route=route_key,
                    fault_kind="latency",
                    requested_delay_ms=latency_ms,
                )
                self.fault_log.append(fault_entry)
                # Call sleep function (may be mocked in tests)
                self.sleep_fn(latency_seconds)
                return False, None

        # No faults injected
        return False, None

    def _check_rate_limit(
        self,
        route_key: str,
        rate_limit_rule: RateLimitRule,
        current_time: float,
    ) -> Optional[FaultLog]:
        """Check if rate limit is exceeded.

        Args:
            route_key: The route identifier.
            rate_limit_rule: The rate limit rule.
            current_time: Current time in seconds.

        Returns:
            A fault log entry if rate limited, None otherwise.
        """
        window_size = rate_limit_rule.window_seconds
        max_requests = rate_limit_rule.requests_per_window

        # Get or create window for this route
        if route_key not in self.rate_limit_windows:
            self.rate_limit_windows[route_key] = []

        window = self.rate_limit_windows[route_key]

        # Remove old entries outside the window
        cutoff_time = current_time - window_size
        window[:] = [(t, c) for t, c in window if t > cutoff_time]

        # Count requests in current window
        request_count = sum(count for _, count in window)

        if request_count >= max_requests:
            # Rate limited
            retry_after = window_size if window else 60
            return FaultLog(
                ordinal=self.request_ordinal,
                route=route_key,
                fault_kind="rate_limit",
                retry_after_seconds=retry_after,
            )

        # Add current request to window
        if window and window[-1][0] == current_time:
            # Same timestamp, increment count
            window[-1] = (current_time, window[-1][1] + 1)
        else:
            # New timestamp
            window.append((current_time, 1))

        return None


class FaultMiddleware(BaseHTTPMiddleware):
    """Middleware for injecting faults into API responses.

    Faults are deterministic based on a seeded random number generator,
    allowing reproducible fault sequences for testing.
    """

    def __init__(
        self,
        app: FastAPI,
        profile: Optional[FaultProfile] = None,
        sleep_fn: Optional[Callable[[float], None]] = None,
        instance: Optional[FaultMiddlewareInstance] = None,
    ) -> None:
        """Initialize the fault injection middleware.

        Args:
            app: The FastAPI application instance.
            profile: The fault profile configuration.
            sleep_fn: Optional callable to simulate delay (for testing).
                If not provided, real time.sleep is used.
            instance: Optional pre-created FaultMiddlewareInstance to share state.
        """
        super().__init__(app)
        if instance is not None:
            # Use the provided shared instance
            self.instance = instance
        elif profile is not None:
            # Create a new instance
            self.instance = FaultMiddlewareInstance(profile, sleep_fn)
        else:
            # No profile and no instance - create empty instance with dummy profile
            from .profile import FaultProfile as FP

            self.instance = FaultMiddlewareInstance(FP(), sleep_fn)

    async def dispatch(self, request: Request, call_next: Callable[..., Any]) -> Response:
        """Dispatch the request through fault injection.

        Args:
            request: The incoming HTTP request.
            call_next: The next middleware or route handler.

        Returns:
            The response, possibly modified with injected faults.
        """
        should_fault, fault_response = self.instance.check_and_inject_fault(request, call_next)
        if should_fault and fault_response is not None:
            return fault_response

        # No faults injected, proceed normally
        return await call_next(request)  # type: ignore[no-any-return]

    def get_fault_log(self) -> list[FaultLog]:
        """Get the current fault log.

        Returns:
            List of fault log entries.
        """
        return self.instance.get_fault_log()


def attach_fault_middleware(
    app: FastAPI,
    profile: FaultProfile,
    sleep_fn: Optional[Callable[[float], None]] = None,
) -> FaultMiddlewareInstance:
    """Attach the fault injection middleware to a FastAPI app.

    Args:
        app: The FastAPI application instance.
        profile: The fault profile configuration.
        sleep_fn: Optional callable to simulate delay (for testing).

    Returns:
        The FaultMiddlewareInstance for accessing the fault log.
    """
    # Create a shared middleware instance
    instance = FaultMiddlewareInstance(profile, sleep_fn)

    # Add middleware to the app with the shared instance
    app.add_middleware(
        cast(Any, FaultMiddleware),
        profile=profile,
        sleep_fn=sleep_fn,
        instance=instance,
    )

    # Store reference for testing
    app.state.fault_middleware_instance = instance

    return instance
