"""AC2 & L1: Loopback socket policy allows inference service base URL."""

import socket

import pytest

pytest_socket = pytest.importorskip("pytest_socket")


@pytest.mark.checklist_id("L1")
def test_inference_service_is_loopback() -> None:
    """L1: Inference service (LM Studio) must be on loopback interface.

    With pytest-socket active, any connection to non-loopback addresses
    is blocked. This test verifies that loopback inference service
    connections succeed but non-loopback inference endpoints are blocked.
    """
    # Test 1: Loopback connections should work (LM Studio at localhost:1234)
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        try:
            # Don't actually connect to a real service, but verify the socket policy
            # allows loopback attempts
            sock.connect(("127.0.0.1", 1234))
        except (socket.timeout, ConnectionRefusedError):
            # Connection refused is OK - means loopback is allowed but nothing listening
            pass
        finally:
            sock.close()
    except Exception as e:
        if "SocketConnectBlockedError" in type(e).__name__:
            pytest.fail(f"Loopback connection to 127.0.0.1 should be allowed: {e}")

    # Test 2: Non-loopback inference endpoints should be blocked
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        try:
            # Try to connect to a non-loopback inference service using literal IP
            # 93.184.216.34 is a stable non-loopback address (example.com)
            sock.connect(("93.184.216.34", 443))
        except (socket.timeout, ConnectionRefusedError):
            # If we got here without SocketConnectBlockedError, the policy didn't block it
            pytest.fail(
                "Non-loopback connection to 93.184.216.34 should be blocked by socket policy"
            )
        finally:
            sock.close()
    except Exception as e:
        if "SocketConnectBlockedError" in type(e).__name__:
            # This is expected - non-loopback should be blocked
            pass
        else:
            error_name = type(e).__name__
            pytest.fail(f"Non-loopback should raise SocketConnectBlockedError, got {error_name}")
