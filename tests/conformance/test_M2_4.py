"""Conformance tests for M2-4: Guard Boundary.

Tests the requirement IDs: R1, R5
"""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from clinicloop.api.app import create_app
from clinicloop.api.guard_boundary import JURISDICTION_SOURCE_HEADER
from clinicloop.evals.guard.corpus_loader import load_cases
from clinicloop.world.generator.snapshot import read_world_snapshot


@pytest.fixture
def world_snapshot(tmp_path: Path) -> Path:
    """Generate a test world snapshot.

    Args:
        tmp_path: Temporary directory fixture from pytest.

    Returns:
        Path to the written snapshot file.
    """
    from clinicloop.world.generator.build import generate_world
    from clinicloop.world.generator.snapshot import write_world_snapshot

    world = generate_world(seed=42, population_size=5, span_days=30)
    snapshot_path = tmp_path / "test_snapshot.json"
    write_world_snapshot(world, snapshot_path)
    return snapshot_path


@pytest.fixture
def client(world_snapshot: Path) -> TestClient:
    """Create a FastAPI test client with a loaded snapshot.

    Args:
        world_snapshot: Path to the snapshot file.

    Returns:
        A TestClient for the app.
    """
    app = create_app(snapshot_path=world_snapshot)
    return TestClient(app)


@pytest.mark.conformance
@pytest.mark.checklist_id("R1")
def test_R1_guard_blocks_product_names(client: TestClient, world_snapshot: Path) -> None:
    """R1: Guard enforces rule AU-G-PRODUCT at runtime.

    The guard must block prescription-only product names from outbound messages
    without checking being optional or deferrable.
    """
    snapshot = read_world_snapshot(world_snapshot)
    cases = load_cases()

    # Find a case that violates AU-G-PRODUCT
    product_cases = [
        c for c in cases if c.expected_rule_id == "AU-G-PRODUCT" and c.expected_verdict == "block"
    ]
    assert len(product_cases) > 0, "Need at least one AU-G-PRODUCT block case"

    case = product_cases[0]
    body = " ".join(msg.text for msg in case.thread if msg.role == "assistant")

    payload = {
        "patient_id": snapshot.patients[0].patient_id,
        "channel": "chat",
        "body": body,
    }
    response = client.post("/messages", json=payload)

    # Must return 422, not 201
    assert response.status_code == 422, (
        f"Expected 422 for product name block, got {response.status_code}"
    )

    # Must include the rule_id
    body_data = response.json()
    assert "AU-G-PRODUCT" in body_data.get("rule_ids", [])


@pytest.mark.conformance
@pytest.mark.checklist_id("R1")
def test_R1_guard_blocks_euphemisms(client: TestClient, world_snapshot: Path) -> None:
    """R1: Guard enforces rule AU-G-EUPHEMISM at runtime.

    The guard must block prescription euphemisms from outbound messages.
    """
    snapshot = read_world_snapshot(world_snapshot)
    cases = load_cases()

    # Find a case that violates AU-G-EUPHEMISM
    euphemism_cases = [
        c for c in cases if c.expected_rule_id == "AU-G-EUPHEMISM" and c.expected_verdict == "block"
    ]
    assert len(euphemism_cases) > 0, "Need at least one AU-G-EUPHEMISM block case"

    case = euphemism_cases[0]
    body = " ".join(msg.text for msg in case.thread if msg.role == "assistant")

    payload = {
        "patient_id": snapshot.patients[0].patient_id,
        "channel": "chat",
        "body": body,
    }
    response = client.post("/messages", json=payload)

    assert response.status_code == 422
    body_data = response.json()
    assert "AU-G-EUPHEMISM" in body_data.get("rule_ids", [])


@pytest.mark.conformance
@pytest.mark.checklist_id("R5")
def test_R5_explicit_uk_jurisdiction_returns_501(client: TestClient, world_snapshot: Path) -> None:
    """R5: Explicit UK jurisdiction returns 501 with RulesetNotImplemented code.

    When an explicit jurisdiction='uk' is specified, the system must return 501
    to signal that the ruleset is not implemented, rather than silently
    applying AU rules or denying the request.
    """
    snapshot = read_world_snapshot(world_snapshot)

    payload = {
        "patient_id": snapshot.patients[0].patient_id,
        "channel": "chat",
        "body": "A benign message",
        "jurisdiction": "uk",
    }
    response = client.post("/messages", json=payload)

    assert response.status_code == 501
    body_data = response.json()
    assert body_data.get("code") == "RulesetNotImplemented"
    assert body_data.get("jurisdiction") == "uk"
    assert JURISDICTION_SOURCE_HEADER in response.headers


@pytest.mark.conformance
@pytest.mark.checklist_id("R5")
def test_R5_explicit_nz_jurisdiction_returns_501(client: TestClient, world_snapshot: Path) -> None:
    """R5: Explicit NZ jurisdiction returns 501 with RulesetNotImplemented code.

    When an explicit jurisdiction='nz' is specified, the system must return 501
    to signal that the ruleset is not implemented.
    """
    snapshot = read_world_snapshot(world_snapshot)

    payload = {
        "patient_id": snapshot.patients[0].patient_id,
        "channel": "chat",
        "body": "A benign message",
        "jurisdiction": "nz",
    }
    response = client.post("/messages", json=payload)

    assert response.status_code == 501
    body_data = response.json()
    assert body_data.get("code") == "RulesetNotImplemented"
    assert body_data.get("jurisdiction") == "nz"
    assert JURISDICTION_SOURCE_HEADER in response.headers


@pytest.mark.conformance
@pytest.mark.checklist_id("R5")
def test_R5_unset_jurisdiction_defaults_to_au_with_flag(
    client: TestClient, world_snapshot: Path
) -> None:
    """R5: Unset jurisdiction defaults to AU with jurisdiction_source='default_au'.

    When jurisdiction is not specified, the system applies AU rules but signals
    the default with jurisdiction_source='default_au' in both the response body
    and header, so the client can detect the automatic fallback.
    """
    snapshot = read_world_snapshot(world_snapshot)

    payload = {
        "patient_id": snapshot.patients[0].patient_id,
        "channel": "chat",
        "body": "A benign message with no violations",
    }
    response = client.post("/messages", json=payload)

    # Request succeeds (benign body)
    assert response.status_code == 201

    body_data = response.json()
    assert body_data.get("jurisdiction_source") == "default_au"
    assert response.headers.get(JURISDICTION_SOURCE_HEADER) == "default_au"
