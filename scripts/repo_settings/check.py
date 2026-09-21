"""Repository settings checker stubs."""


def check_settings(payload_path: str | None = None) -> int:
    """Check repository settings.

    Args:
        payload_path: Path to repository payload JSON file, or None to read from stdin.

    Returns:
        Exit code 0 if compliant, 1 if non-compliant.
    """
    return 2


def check_protection(payload_path: str | None = None) -> int:
    """Check branch protection settings.

    Args:
        payload_path: Path to protection payload JSON file, or None to read from stdin.

    Returns:
        Exit code 0 if compliant, 1 if non-compliant.
    """
    return 2


def check_token_scopes(payload_path: str | None = None) -> int:
    """Check token scopes.

    Args:
        payload_path: Path to token scopes file, or None to read from stdin.

    Returns:
        Exit code 0 if compliant, 1 if non-compliant.
    """
    return 2
