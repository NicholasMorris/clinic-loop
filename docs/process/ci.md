# Continuous Integration and Local Gate

This document describes the local CI gate and the conformance testing infrastructure that verify requirement compliance before code is merged.

## The Local Gate: `make ci`

The `make ci` target is the local gate that runs before every push. It executes in this order:

1. **ruff check** — Lints the codebase for style and correctness issues
2. **ruff format --check** — Verifies consistent formatting
3. **mypy** — Type checks with strict mode enabled
4. **pytest -m "not local_model"** — Runs unit tests, excluding tests that require a running LLM server
5. **Discovers and executes all executable shell scripts in checks/ in lexical filename order**

If any step fails, the gate exits with a non-zero status and subsequent steps do not run.

## Pre-Push Hook

The `.githooks/pre-push` hook is installed via `make hooks` and runs `make ci` in a clean checkout of the merge base before allowing a push to proceed. This ensures the branch is ready for CI without network dependencies.

## Checks Discovery

The Makefile uses a glob pattern to discover executable shell scripts under `checks/`:

```bash
for check in checks/*.sh; do
    [ -x "$check" ] || continue
    "$check" || exit $?
done
```

Scripts are executed in lexical filename order (e.g., `checks/a-first.sh` before `checks/z-last.sh`). Each script must exit with status 0 to pass; any non-zero exit stops the gate.

Later issues add check scripts for their own requirements. The Makefile itself is never edited to add new checks; discovery is automatic.

## Conformance Testing

Every requirement in the brief is verified by a conformance test. Conformance tests live in `tests/conformance/` and are organized by requirement identifier.

### The Checklist ID Marker

Each conformance test module carries a pytest marker identifying the requirement it verifies:

```python
import pytest

@pytest.mark.checklist_id("B1")
def test_repository_is_public_python_312() -> None:
    # Test body
```

The marker is a string containing the requirement ID (e.g., `"B1"`, `"D6"`, `"L1"`).

### One File Per Identifier

The rule is: **one conformance test file per requirement identifier**.

- `tests/conformance/test_B1.py` verifies requirement B1
- `tests/conformance/test_D6.py` verifies requirement D6
- And so on

If a requirement has multiple acceptance criteria, they may be separate test functions within the same file. All functions that verify that requirement must carry the same `@pytest.mark.checklist_id()` marker.

### The Coverage Registry

The registry (`tests/conformance/registry.py`) discovers all conformance test modules and builds a mapping from requirement identifiers to test node IDs:

```python
from tests.conformance.registry import build_coverage_report

report = build_coverage_report()
# Returns: {"B1": ["tests/conformance/test_B1.py::test_..."], "D6": [...], ...}
```

The registry test (`tests/conformance/test_registry.py`) verifies that:

1. Every conformance module declares a checklist_id marker
2. The five registered identifiers (B1, D6, L1, L6, P4) all have test coverage
3. Fixture identifiers (like ZZ9) can be discovered and mapped correctly

### Requirement IDs Registered Here

M0-2 registers exactly five requirement identifiers:

- **B1** — Repository is public, Python 3.12, package name is clinicloop
- **D6** — ruff and mypy pass with Google-style docstrings configured
- **L1** — Inference service base URL is loopback-only
- **L6** — Cloud speech service endpoints are blocked
- **P4** — Changes include both a changelog fragment and documentation edits

Each identifier has its own conformance test module, listed in the issue's "Files (write-allowed)" section.

## Socket Policy

All tests run with pytest-socket configured to allow loopback interfaces only:

- `127.0.0.1` (IPv4 loopback)
- `::1` (IPv6 loopback)
- `localhost` (loopback hostname)

Any attempt to connect to a non-loopback address will raise `SocketConnectBlockedError`. This prevents tests from accidentally reaching the public internet or cloud services.

The policy is set up in the root `conftest.py` as an autouse fixture that runs once per test session.

## Test Execution

Tests are run by pytest and include:

- Unit tests for business logic
- Conformance tests verifying requirement compliance
- Integration tests verifying multiple components work together

Tests that require the LLM model server running are marked with `@pytest.mark.local_model` and are excluded from `make ci` (they run only in local evaluation workflows).

## Type Hints and Documentation

All code is written with full type hints, and all public functions and classes have Google-style docstrings. Both ruff (with the D rule set) and mypy strict mode enforce these requirements.
