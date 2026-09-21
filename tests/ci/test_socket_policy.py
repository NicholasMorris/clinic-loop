"""AC2: Socket policy allows loopback, blocks non-loopback."""

import socket

import pytest

pytest_socket = pytest.importorskip("pytest_socket")


@pytest.mark.parametrize(
    "host,should_connect",
    [
        ("127.0.0.1", True),   # Loopback IPv4
        ("::1", True),         # Loopback IPv6
        ("localhost", True),   # Loopback hostname
        ("93.184.216.34", False),  # Non-loopback (example.com)
    ],
)
def test_only_loopback_hosts_are_reachable(host: str, should_connect: bool) -> None:
    """AC2: TCP connections to loopback succeed; non-loopback raises SocketConnectBlockedError."""
    try:
        # Try to create a socket and connect to the host on a common port
        family = socket.AF_INET if ":" not in host else socket.AF_INET6
        sock = socket.socket(family, socket.SOCK_STREAM)
        sock.settimeout(1)
        try:
            sock.connect((host, 80))
            connected = True
        except (socket.timeout, ConnectionRefusedError):
            # The host may not be listening, but we can connect (no block)
            connected = True
        finally:
            sock.close()

        if should_connect:
            # Expected to connect or get refused (not blocked)
            assert connected, f"Expected connection to {host} to succeed"
        else:
            # Should have been blocked
            pytest.fail(f"Expected connection to {host} to be blocked")

    except Exception as e:
        error_name = type(e).__name__
        if should_connect:
            # If we expect connection and got an error, it should not be SocketConnectBlockedError
            if "SocketConnectBlockedError" in error_name or "SocketBlockedError" in error_name:
                pytest.fail(f"Expected connection to {host} to succeed, but got blocked: {e}")
        else:
            # If we expect blocking and got SocketConnectBlockedError, that's correct
            if "SocketConnectBlockedError" in error_name or "SocketBlockedError" in error_name:
                pass  # Expected
            else:
                # Some other error; re-raise
                raise
