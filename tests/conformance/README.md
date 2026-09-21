# Conformance Tests

Conformance tests verify that the codebase meets every requirement in the project brief. Each requirement identifier has its own test module.

## Structure

- `test_B1.py` — Verifies repository settings, Python version, and package name
- `test_D6.py` — Verifies linting and type checking with Google-style docstrings
- `test_L1.py` — Verifies inference service endpoint is loopback-only
- `test_L6.py` — Verifies cloud speech services are blocked
- `test_P4.py` — Verifies changelog and documentation requirements
- `test_registry.py` — Verifies the conformance registry is complete
- `data/` — Fixtures and test data (e.g., recorded API responses)

## Adding Tests for New Requirements

When adding a new requirement:

1. Create a test module named `test_<ID>.py` (e.g., `test_G1.py` for requirement G1)
2. Import `pytest` and write test functions
3. Mark each test function with `@pytest.mark.checklist_id("<ID>")`
4. Add the module to the issue's "Files (write-allowed)" list
5. The registry will automatically discover and catalog the test

Example:

```python
import pytest

@pytest.mark.checklist_id("G1")
def test_g1_requirement() -> None:
    """Verify G1 requirement is met."""
    # Test body
```

## Socket Policy

All conformance tests run with pytest-socket configured to allow loopback interfaces only. Tests that would reach non-loopback addresses will raise `SocketConnectBlockedError` unless the address is explicitly allowed.

The loopback allowlist is configured in the root `conftest.py` as a session-scope autouse fixture.

## Coverage Report

The `registry.build_coverage_report()` function returns a dictionary mapping each requirement identifier to the test node IDs that verify it. The test registry verifies that every required identifier has at least one test.
