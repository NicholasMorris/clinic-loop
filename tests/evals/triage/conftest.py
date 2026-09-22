"""Fixtures for triage evaluation tests."""

import pytest

pytest_socket = pytest.importorskip("pytest_socket")


@pytest.fixture
def disable_socket() -> None:
    """Disable non-loopback sockets for offline testing."""
    # Allow only loopback hosts before disabling
    pytest_socket.socket_allow_hosts(
        ["127.0.0.1", "::1"],
        allow_unix_socket=False,
    )
    pytest_socket.disable_socket()
