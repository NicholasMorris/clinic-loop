"""Fault profile loading and validation."""

from pathlib import Path

from pydantic import BaseModel


class FaultProfile(BaseModel):
    """Configuration for fault injection.

    Attributes:
        seed: Random seed for reproducible fault sequences.
        routes: Dict mapping route patterns to route-specific fault rules.
    """

    seed: int = 0
    routes: dict[str, "RouteFaultRules"] = {}


class RouteFaultRules(BaseModel):
    """Fault rules for a specific route.

    Attributes:
        latency: Optional latency injection rule.
        server_error: Optional server error injection rule.
        rate_limit: Optional rate limiting rule.
    """

    latency: "LatencyRule | None" = None
    server_error: "ServerErrorRule | None" = None
    rate_limit: "RateLimitRule | None" = None


class LatencyRule(BaseModel):
    """Latency injection rule.

    Attributes:
        probability: Probability of injecting latency (0.0 to 1.0).
        latency_ms: Requested delay in milliseconds.
    """

    probability: float = 0.0
    latency_ms: int = 0


class ServerErrorRule(BaseModel):
    """Server error injection rule.

    Attributes:
        probability: Probability of injecting error (0.0 to 1.0).
        status: HTTP status code to return (e.g., 503).
    """

    probability: float = 0.0
    status: int = 503


class RateLimitRule(BaseModel):
    """Rate limiting rule.

    Attributes:
        probability: Probability of enforcing rate limit (0.0 to 1.0).
        requests_per_window: Number of requests allowed per time window.
        window_seconds: Time window duration in seconds.
    """

    probability: float = 0.0
    requests_per_window: int = 0
    window_seconds: int = 60


class UnknownFaultRoute(Exception):
    """Raised when a fault profile references an unknown route."""

    pass


def load_profile(profile_data: dict, app_routes: set[str]) -> FaultProfile:
    """Load and validate a fault profile configuration.

    Validates that all routes specified in the profile exist in the app.

    Args:
        profile_data: Dictionary containing fault profile configuration.
        app_routes: Set of available routes in the app (e.g., {"GET /orders"}).

    Returns:
        A validated FaultProfile instance.

    Raises:
        UnknownFaultRoute: If a route in the profile is not in app_routes.
        NotImplementedError: Stub implementation.
    """
    raise NotImplementedError("load_profile stub")


# Update forward references for pydantic models
FaultProfile.model_rebuild()
RouteFaultRules.model_rebuild()
