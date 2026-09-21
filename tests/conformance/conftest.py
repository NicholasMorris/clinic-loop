"""Fixtures and configuration for conformance tests."""

import pytest


def checklist_id(identifier: str) -> None:
    """Marker helper to associate a test module with a requirement identifier.

    Args:
        identifier: The requirement ID (e.g., "B1", "D6", "L1", "L6", "P4").
    """
    pytest.mark.checklist_id(identifier)
