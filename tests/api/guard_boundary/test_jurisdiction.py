"""Test AC3: jurisdiction handling."""

from pathlib import Path

from fastapi.testclient import TestClient

from clinicloop.api.guard_boundary import JURISDICTION_SOURCE_HEADER
from clinicloop.world.generator.snapshot import read_world_snapshot


def test_explicit_unimplemented_region_returns_501_and_default_is_flagged(
    client: TestClient,
    world_snapshot: Path,
) -> None:
    """Test jurisdiction handling.

    AC3: POST /messages with jurisdiction="uk" and with jurisdiction="nz"
    each return 501 with body code "RulesetNotImplemented"; with
    jurisdiction unset the response is the AU result with body field
    jurisdiction_source == "default_au" and a response header whose name
    the test imports from the single constant exported by
    api/guard_boundary.py.

    Args:
        client: TestClient fixture.
        world_snapshot: Path to snapshot.
    """
    snapshot = read_world_snapshot(world_snapshot)
    patient_id = snapshot.patients[0].patient_id

    # Test UK jurisdiction returns 501
    payload_uk = {
        "patient_id": patient_id,
        "channel": "chat",
        "body": "Hello from UK",
        "jurisdiction": "uk",
    }
    response = client.post("/messages", json=payload_uk)
    assert response.status_code == 501, (
        f"UK jurisdiction: expected 501, got {response.status_code}. Body: {response.text}"
    )
    body = response.json()
    assert body.get("code") == "RulesetNotImplemented", (
        f"UK: expected code 'RulesetNotImplemented', got {body.get('code')}"
    )
    assert JURISDICTION_SOURCE_HEADER in response.headers

    # Test NZ jurisdiction returns 501
    payload_nz = {
        "patient_id": patient_id,
        "channel": "chat",
        "body": "Hello from NZ",
        "jurisdiction": "nz",
    }
    response = client.post("/messages", json=payload_nz)
    assert response.status_code == 501, (
        f"NZ jurisdiction: expected 501, got {response.status_code}. Body: {response.text}"
    )
    body = response.json()
    assert body.get("code") == "RulesetNotImplemented", (
        f"NZ: expected code 'RulesetNotImplemented', got {body.get('code')}"
    )
    assert JURISDICTION_SOURCE_HEADER in response.headers

    # Test unset jurisdiction falls back to AU with default_au source
    payload_unset = {
        "patient_id": patient_id,
        "channel": "chat",
        "body": "Hello without jurisdiction",
    }
    response = client.post("/messages", json=payload_unset)
    # When unset, should be allowed (assuming benign body) or blocked with AU rules
    # The key assertion is the jurisdiction_source
    assert response.status_code in (201, 422), (
        f"Unset jurisdiction: expected 201 or 422, got {response.status_code}"
    )
    body = response.json()
    assert body.get("jurisdiction_source") == "default_au", (
        f"Unset: expected jurisdiction_source 'default_au', got {body.get('jurisdiction_source')}"
    )
    assert JURISDICTION_SOURCE_HEADER in response.headers
    assert response.headers[JURISDICTION_SOURCE_HEADER] == "default_au"

    # Test explicit AU jurisdiction returns request source
    payload_explicit_au = {
        "patient_id": patient_id,
        "channel": "chat",
        "body": "Hello from explicit AU",
        "jurisdiction": "au",
    }
    response = client.post("/messages", json=payload_explicit_au)
    assert response.status_code in (201, 422), (
        f"Explicit AU: expected 201 or 422, got {response.status_code}"
    )
    body = response.json()
    source = body.get("jurisdiction_source")
    assert source == "request", f"Explicit AU: expected jurisdiction_source 'request', got {source}"
    assert JURISDICTION_SOURCE_HEADER in response.headers
    assert response.headers[JURISDICTION_SOURCE_HEADER] == "request"

    # Test unknown jurisdiction returns 400
    payload_unknown = {
        "patient_id": patient_id,
        "channel": "chat",
        "body": "Hello from unknown",
        "jurisdiction": "xx",
    }
    response = client.post("/messages", json=payload_unknown)
    assert response.status_code == 400, (
        f"Unknown jurisdiction: expected 400, got {response.status_code}. Body: {response.text}"
    )
    body = response.json()
    assert body.get("code") == "UnknownJurisdiction", (
        f"Unknown: expected code 'UnknownJurisdiction', got {body.get('code')}"
    )
    assert JURISDICTION_SOURCE_HEADER in response.headers
