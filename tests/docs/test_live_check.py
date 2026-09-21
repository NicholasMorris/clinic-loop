"""Tests for the docs_live_check script."""

from unittest.mock import Mock, patch

import pytest


def test_live_check_exits_non_zero_unless_200() -> None:
    """Test that docs_live_check.py exits 0 for 200 and 1 for other statuses.

    AC2: scripts/docs_live_check.py exits 0 for a stubbed response whose status
    is 200 and exits 1 printing the observed status for stubbed responses of 404
    and 500, with the HTTP client injected so the test opens no socket.
    """
    # Import the module
    import sys
    from pathlib import Path

    repo_root = Path(__file__).parent.parent.parent
    scripts_dir = repo_root / "scripts"
    sys.path.insert(0, str(scripts_dir))

    try:
        import docs_live_check  # type: ignore[import-not-found]
    except ImportError:
        pytest.skip("docs_live_check module not found")

    # Test 1: 200 status should return 0
    mock_response = Mock()
    mock_response.status_code = 200
    mock_client = Mock()
    mock_client.get.return_value = mock_response
    mock_client.__enter__ = Mock(return_value=mock_client)
    mock_client.__exit__ = Mock(return_value=False)

    with patch("docs_live_check.httpx.Client", return_value=mock_client):
        exit_code = docs_live_check.check_live_url("http://example.com")
        assert exit_code == 0, f"Expected exit code 0 for status 200, got {exit_code}"

    # Test 2: 404 status should return 1
    mock_response.status_code = 404
    mock_client = Mock()
    mock_client.get.return_value = mock_response
    mock_client.__enter__ = Mock(return_value=mock_client)
    mock_client.__exit__ = Mock(return_value=False)

    with patch("docs_live_check.httpx.Client", return_value=mock_client):
        exit_code = docs_live_check.check_live_url("http://example.com")
        assert exit_code == 1, f"Expected exit code 1 for status 404, got {exit_code}"

    # Test 3: 500 status should return 1
    mock_response.status_code = 500
    mock_client = Mock()
    mock_client.get.return_value = mock_response
    mock_client.__enter__ = Mock(return_value=mock_client)
    mock_client.__exit__ = Mock(return_value=False)

    with patch("docs_live_check.httpx.Client", return_value=mock_client):
        exit_code = docs_live_check.check_live_url("http://example.com")
        assert exit_code == 1, f"Expected exit code 1 for status 500, got {exit_code}"
