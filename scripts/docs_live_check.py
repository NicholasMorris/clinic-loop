#!/usr/bin/env python3
"""Check that the published docs site returns HTTP 200.

This script verifies that the documentation site published to GitHub Pages
is accessible and returns a 200 status code.
"""

import sys

import httpx


def check_live_url(url: str) -> int:
    """Check if a URL returns HTTP 200.

    Args:
        url: The URL to check.

    Returns:
        0 if the URL returns 200, 1 otherwise.
    """
    try:
        with httpx.Client() as client:
            response = client.get(url, follow_redirects=True, timeout=10.0)
            if response.status_code == 200:
                print(f"✓ {url} returned 200 OK")
                return 0
            else:
                print(
                    f"✗ {url} returned {response.status_code}",
                    file=sys.stderr,
                )
                return 1
    except httpx.RequestError as e:
        print(f"✗ Request failed: {e}", file=sys.stderr)
        return 1


def main() -> int:
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: docs_live_check.py <URL>", file=sys.stderr)
        return 1

    url = sys.argv[1]
    return check_live_url(url)


if __name__ == "__main__":
    sys.exit(main())
