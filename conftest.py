"""Root pytest configuration."""

import pytest


@pytest.fixture(scope="session", autouse=True)
def enable_socket_policy() -> None:
    """Enable pytest-socket with loopback-only policy."""
    pytest_socket = pytest.importorskip("pytest_socket")

    # Allow loopback interfaces only, which implicitly disables other hosts
    pytest_socket.socket_allow_hosts(allowed=["127.0.0.1", "::1", "localhost"])
