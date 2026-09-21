"""Root pytest configuration."""

import socket as socket_module

import pytest


def pytest_configure(config):
    """Configure pytest-socket to allow only loopback."""
    # Ensure pytest-socket is available
    pytest.importorskip("pytest_socket")

    # Resolve loopback hosts and build the resolution cache
    resolution_cache = {}
    for host in ["127.0.0.1", "::1", "localhost"]:
        try:
            addrs = socket_module.getaddrinfo(host, None)
            resolution_cache[host] = {addr[-1][0] for addr in addrs}
        except socket_module.gaierror:
            pass

    # Store the configuration in config for pytest_runtest_setup to use
    config._pytest_socket_allowed_hosts = ["127.0.0.1", "::1", "localhost"]
    config._pytest_socket_resolution_cache = resolution_cache


def pytest_runtest_setup(item):
    """Apply socket policy at test setup time."""
    # Get pytest-socket module
    try:
        pytest_socket = pytest.importorskip("pytest_socket")
    except Exception:
        return

    # Check if this test should have socket blocking
    config = item.config
    if hasattr(config, "_pytest_socket_allowed_hosts"):
        # Apply the loopback-only socket policy
        pytest_socket.socket_allow_hosts(
            allowed=config._pytest_socket_allowed_hosts,
            resolution_cache=config._pytest_socket_resolution_cache,
        )
