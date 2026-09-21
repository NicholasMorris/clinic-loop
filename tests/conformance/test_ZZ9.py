"""Fixture conformance module for testing the registry mechanism."""

import pytest


@pytest.mark.checklist_id("ZZ9")
def test_fixture_declaration() -> None:
    """Fixture test that declares the synthetic identifier ZZ9.

    This test exists only to verify that the registry mechanism can discover
    and map synthetic identifiers like ZZ9 to their test node IDs.
    """
    assert True
