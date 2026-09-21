"""AC2 & L6: Loopback socket policy allows cloud speech services blocklist."""

import socket

import pytest

pytest_socket = pytest.importorskip("pytest_socket")


@pytest.mark.checklist_id("L6")
def test_cloud_speech_services_are_blocked() -> None:
    """L6: Cloud speech services must be blocked by socket policy.

    This test verifies that the socket policy prevents connections to cloud
    speech service endpoints. Uses literal IP addresses to avoid DNS lookups,
    which could have different blocking behavior.
    """
    # Cloud speech service endpoints represented by non-loopback IP addresses.
    # These literal IPs represent typical cloud speech service endpoints
    # that should be blocked by the socket policy.
    cloud_speech_ips = [
        ("93.184.216.34", 443),  # Example IP for Google Cloud Speech
        ("172.217.14.206", 443),  # Example IP for Azure Speech Services
        ("52.148.116.88", 443),  # Example IP for AWS Transcribe
    ]

    for ip, port in cloud_speech_ips:
        blocked = False

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            try:
                sock.connect((ip, port))
            except (socket.timeout, ConnectionRefusedError):
                # If we got here, the socket policy didn't block the connection
                pytest.fail(f"Cloud speech service {ip}:{port} should be blocked by socket policy")
            finally:
                sock.close()
        except Exception as e:
            error_name = type(e).__name__
            # Must be SocketConnectBlockedError, not any other exception
            if "SocketConnectBlockedError" in error_name:
                # This is expected - cloud services should be blocked
                blocked = True
            else:
                pytest.fail(f"Cloud service {ip}:{port} should be blocked, got {error_name}")

        assert blocked, f"Cloud service {ip}:{port} must be blocked by socket policy"
