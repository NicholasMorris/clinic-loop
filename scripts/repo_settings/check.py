"""Repository settings checker."""

import json
import sys

from .review_contexts import REQUIRED_STATUS_CONTEXTS, REQUIRED_TOKEN_SCOPES


def _load_json_payload(payload_path: str | None = None) -> dict:
    """Load JSON payload from file or stdin.

    Args:
        payload_path: Path to JSON file, or None to read from stdin.

    Returns:
        Parsed JSON object as dictionary.
    """
    if payload_path:
        with open(payload_path) as f:
            return json.load(f)
    else:
        return json.load(sys.stdin)


def _load_text_payload(payload_path: str | None = None) -> str:
    """Load text payload from file or stdin.

    Args:
        payload_path: Path to text file, or None to read from stdin.

    Returns:
        Text content.
    """
    if payload_path:
        with open(payload_path) as f:
            return f.read()
    else:
        return sys.stdin.read()


def check_settings(payload_path: str | None = None) -> int:
    """Check repository settings.

    Validates that the repository has:
    - visibility: "public"
    - default_branch: "main"
    - name: "clinic-loop"
    - pages.build_type: "legacy"
    - pages.source.branch: "gh-pages"

    Args:
        payload_path: Path to repository payload JSON file, or None to read from stdin.

    Returns:
        Exit code 0 if compliant, 1 if non-compliant.
    """
    payload = _load_json_payload(payload_path)

    expected = {
        "visibility": "public",
        "default_branch": "main",
        "name": "clinic-loop",
        "pages.build_type": "legacy",
        "pages.source.branch": "gh-pages",
    }

    departures = []

    # Check top-level fields
    if payload.get("visibility") != expected["visibility"]:
        departures.append(
            f"visibility: expected '{expected['visibility']}', got '{payload.get('visibility')}'"
        )

    if payload.get("default_branch") != expected["default_branch"]:
        departures.append(
            f"default_branch: expected '{expected['default_branch']}', "
            f"got '{payload.get('default_branch')}'"
        )

    if payload.get("name") != expected["name"]:
        departures.append(f"name: expected '{expected['name']}', got '{payload.get('name')}'")

    # Check nested pages fields
    pages = payload.get("pages", {})
    if pages.get("build_type") != expected["pages.build_type"]:
        departures.append(
            f"build_type: expected '{expected['pages.build_type']}', "
            f"got '{pages.get('build_type')}'"
        )

    source = pages.get("source", {})
    if source.get("branch") != expected["pages.source.branch"]:
        departures.append(
            f"source_branch: expected '{expected['pages.source.branch']}', "
            f"got '{source.get('branch')}'"
        )

    # Print departures and return appropriate exit code
    if departures:
        for departure in departures:
            print(departure)
        return 1

    return 0


def check_protection(payload_path: str | None = None) -> int:
    """Check branch protection settings.

    Validates that all required status contexts are present.

    Args:
        payload_path: Path to protection payload JSON file, or None to read from stdin.

    Returns:
        Exit code 0 if compliant, 1 if non-compliant.
    """
    payload = _load_json_payload(payload_path)

    required_checks = payload.get("required_status_checks", {})
    contexts = set(required_checks.get("contexts", []))
    required_contexts = set(REQUIRED_STATUS_CONTEXTS)

    missing = required_contexts - contexts

    if missing:
        for context in sorted(missing):
            print(f"missing required status context: {context}")
        return 1

    return 0


def check_token_scopes(payload_path: str | None = None) -> int:
    """Check token scopes.

    Validates that X-OAuth-Scopes header includes all required scopes.

    Args:
        payload_path: Path to file containing X-OAuth-Scopes header, or None to read from stdin.

    Returns:
        Exit code 0 if compliant, 1 if non-compliant.
    """
    content = _load_text_payload(payload_path)

    # Parse the X-OAuth-Scopes header
    scopes_str = ""
    for line in content.split("\n"):
        if line.startswith("X-OAuth-Scopes:"):
            scopes_str = line.split(":", 1)[1].strip()
            break

    # Parse scopes from comma-separated list
    scopes = {s.strip() for s in scopes_str.split(",") if s.strip()}
    required_scopes = set(REQUIRED_TOKEN_SCOPES)

    missing = required_scopes - scopes

    if missing:
        for scope in sorted(missing):
            print(f"missing required scope: {scope}")
        return 1

    return 0
