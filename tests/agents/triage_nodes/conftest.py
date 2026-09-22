"""Fixtures for triage node tests."""

import json
from pathlib import Path

import pytest


@pytest.fixture
def cassette_dir() -> Path:
    """Get the cassettes directory."""
    return Path(__file__).parent / "cassettes"


@pytest.fixture
def fixtures_dir() -> Path:
    """Get the fixtures directory."""
    return Path(__file__).parent / "fixtures"
