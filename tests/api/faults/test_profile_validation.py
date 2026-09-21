"""Tests for fault profile validation."""

import pytest

from clinicloop.api.faults.profile import (
    UnknownFaultRoute,
    load_profile,
)


def test_unknown_route_rejected_at_load() -> None:
    """Test that unknown routes in profile raise UnknownFaultRoute at load time.

    Acceptance criterion AC6: A profile naming a route the app does not serve
    raises UnknownFaultRoute at load time, with the offending route string in
    the message.
    """
    # Profile with a route that doesn't exist
    profile_data = {
        "seed": 42,
        "routes": {"GET /nonexistent": {"server_error": {"probability": 1.0, "status": 503}}},
    }

    # Valid app routes
    app_routes = {"GET /orders", "GET /patients", "GET /consults", "GET /messages"}

    # Should raise UnknownFaultRoute with the invalid route in the message
    with pytest.raises(UnknownFaultRoute) as exc_info:
        load_profile(profile_data, app_routes)

    # Check that the exception message contains the invalid route
    assert "GET /nonexistent" in str(exc_info.value)


def test_load_profile_with_valid_routes() -> None:
    """Test that a profile with all valid routes loads successfully.

    This tests the happy path of load_profile with valid routes.
    """
    profile_data = {
        "seed": 42,
        "routes": {"GET /orders": {"server_error": {"probability": 1.0, "status": 503}}},
    }

    app_routes = {"GET /orders", "GET /patients", "GET /consults", "GET /messages"}

    # Should not raise
    profile = load_profile(profile_data, app_routes)
    assert profile is not None
    assert profile.seed == 42
