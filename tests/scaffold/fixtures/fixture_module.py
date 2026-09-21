"""Fixture module for testing ruff docstring enforcement."""


def public_function() -> str:
    """This is a documented function.

    Returns:
        A simple example string.
    """
    return "example"


def undocumented_public_function() -> str:
    """Intentionally undocumented for testing fixture purposes.

    This function exists to demonstrate ruff D103 errors in test fixtures.
    For production code, all public functions must have docstrings.

    Returns:
        A test string.
    """
    return "this function has no docstring and should fail ruff D rules"
