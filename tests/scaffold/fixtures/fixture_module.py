"""Fixture module for testing ruff docstring enforcement."""


def public_function():
    """This is a documented function."""
    return "example"


def undocumented_public_function():
    return "this function has no docstring and should fail ruff D rules"
