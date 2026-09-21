"""AC2: Socket policy allows loopback, blocks non-loopback."""

import socket

import pytest

pytest_socket = pytest.importorskip("pytest_socket")


@pytest.mark.parametrize(
    "host,should_connect",
    [
        ("127.0.0.1", True),  # Loopback IPv4
        ("::1", True),  # Loopback IPv6
        ("localhost", True),  # Loopback hostname
        ("93.184.216.34", False),  # Non-loopback address (example.com IP)
    ],
)
def test_only_loopback_hosts_are_reachable(host: str, should_connect: bool) -> None:
    """AC2: TCP connections to loopback succeed; non-loopback raises SocketConnectBlockedError."""
    blocked_error_raised = False
    other_error = None

    try:
        # Try to create a socket and connect to the host on a common port
        family = socket.AF_INET if ":" not in host else socket.AF_INET6
        sock = socket.socket(family, socket.SOCK_STREAM)
        sock.settimeout(1)
        try:
            sock.connect((host, 53))
        except (socket.timeout, ConnectionRefusedError):
            # The host may not be listening, but connection attempt succeeded (no block)
            pass
        finally:
            sock.close()

    except Exception as e:
        error_name = type(e).__name__
        if "SocketConnectBlockedError" in error_name or "SocketBlockedError" in error_name:
            blocked_error_raised = True
        else:
            other_error = (error_name, str(e))

    # Verify the result matches expectations
    if should_connect:
        # For loopback, we should NOT get a blocking error
        if blocked_error_raised:
            pytest.fail(f"Expected loopback {host} to be allowed, but got blocked")
        if other_error:
            pytest.fail(f"Unexpected error for loopback {host}: {other_error[0]}: {other_error[1]}")
    else:
        # For non-loopback, we MUST get a blocking error
        if not blocked_error_raised:
            pytest.fail(
                f"Expected non-loopback {host} to be blocked by socket policy, but it was not"
            )
        if other_error:
            # If we got a different error, report it
            err_type, err_msg = other_error
            pytest.fail(f"Expected block for {host}, got {err_type}: {err_msg}")
