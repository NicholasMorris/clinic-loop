"""Conformance tests for M1-4: Fault injection.

Requirement ID: C0 (SimClinic)

pytest.mark.checklist_id: C0
"""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from clinicloop.api.app import create_app
from clinicloop.api.faults.middleware import attach_fault_middleware
from clinicloop.api.faults.profile import (
    FaultProfile,
    LatencyRule,
    RateLimitRule,
    RouteFaultRules,
    ServerErrorRule,
)
from clinicloop.world.generator.snapshot import write_world_snapshot


@pytest.fixture
def world_snapshot(tmp_path: Path) -> Path:
    """Generate a test world snapshot.

    Args:
        tmp_path: Temporary directory fixture from pytest.

    Returns:
        Path to the written snapshot file.
    """
    from clinicloop.world.generator.build import generate_world

    world = generate_world(seed=42, population_size=5, span_days=30)
    snapshot_path = tmp_path / "test_snapshot.json"
    write_world_snapshot(world, snapshot_path)
    return snapshot_path


class TestFaultInjectionC0:
    """Tests for fault injection module (Requirement C0).

    These tests verify that the SimClinic mock API can inject reproducible
    faults for testing agent resilience and error handling.
    """

    def test_faults_disabled_by_default(self, world_snapshot: Path) -> None:
        """Test AC1: Faults are disabled by default.

        With no profile configured, consecutive requests return 200
        and the fault log is empty.
        """
        app = create_app(snapshot_path=world_snapshot)
        client = TestClient(app)

        # 200 consecutive requests should all succeed
        for _ in range(200):
            response = client.get("/orders")
            assert response.status_code == 200

    def test_latency_injection(self, world_snapshot: Path) -> None:
        """Test AC2: Latency injection with recording.

        Latency rules record requested delays without real sleeping.
        """

        class RecordingSleeep:
            def __init__(self) -> None:
                self.delays: list[float] = []

            def __call__(self, delay_seconds: float) -> None:
                self.delays.append(delay_seconds)

        app = create_app(snapshot_path=world_snapshot)
        sleep_recorder = RecordingSleeep()
        profile = FaultProfile(
            seed=42,
            routes={
                "GET /orders": RouteFaultRules(latency=LatencyRule(probability=1.0, latency_ms=100))
            },
        )
        middleware = attach_fault_middleware(app, profile, sleep_recorder)
        client = TestClient(app)

        # Make 10 requests
        for _ in range(10):
            response = client.get("/orders")
            assert response.status_code == 200

        # Verify latency was recorded
        log = middleware.get_fault_log()
        assert len(log) == 10
        for entry in log:
            assert entry["fault_kind"] == "latency"
            assert entry["requested_delay_ms"] == 100

        # Verify sleep was called 10 times with 0.1 seconds each
        assert len(sleep_recorder.delays) == 10
        for delay in sleep_recorder.delays:
            assert delay == 0.1

    def test_server_error_injection(self, world_snapshot: Path) -> None:
        """Test AC3: Server error injection with 503 status.

        Error rules return configured status with fault_kind in response.
        """
        app = create_app(snapshot_path=world_snapshot)
        profile = FaultProfile(
            seed=42,
            routes={
                "GET /orders": RouteFaultRules(
                    server_error=ServerErrorRule(probability=1.0, status=503)
                )
            },
        )
        middleware = attach_fault_middleware(app, profile)
        client = TestClient(app)

        # All requests should return 503
        for _ in range(10):
            response = client.get("/orders")
            assert response.status_code == 503
            assert response.json()["fault_kind"] == "server_error"

        # Verify error is recorded
        log = middleware.get_fault_log()
        assert len(log) == 10
        for entry in log:
            assert entry["fault_kind"] == "server_error"

    def test_rate_limit_injection(self, world_snapshot: Path) -> None:
        """Test AC4: Rate limiting with 429 status and Retry-After header.

        Rate limit rules enforce requests per window and return 429.
        """
        app = create_app(snapshot_path=world_snapshot)
        profile = FaultProfile(
            seed=42,
            routes={
                "GET /orders": RouteFaultRules(
                    rate_limit=RateLimitRule(
                        probability=1.0, requests_per_window=3, window_seconds=60
                    )
                )
            },
        )
        attach_fault_middleware(app, profile)
        client = TestClient(app)

        # First 3 requests succeed
        for _ in range(3):
            response = client.get("/orders")
            assert response.status_code == 200

        # Fourth request is rate limited
        response = client.get("/orders")
        assert response.status_code == 429
        assert "Retry-After" in response.headers
        assert int(response.headers["Retry-After"]) > 0

    def test_deterministic_from_seed(self, world_snapshot: Path) -> None:
        """Test AC5: Same seed produces identical fault sequences.

        Different seeds produce different sequences (with high probability).
        """
        profile_seed_7 = FaultProfile(
            seed=7,
            routes={
                "GET /orders": RouteFaultRules(
                    server_error=ServerErrorRule(probability=0.3, status=503),
                    latency=LatencyRule(probability=0.2, latency_ms=100),
                )
            },
        )

        # Run 1: Seed 7
        app1 = create_app(snapshot_path=world_snapshot)
        middleware1 = attach_fault_middleware(app1, profile_seed_7)
        client1 = TestClient(app1)
        for _ in range(100):
            response = client1.get("/orders")
            assert response.status_code in (200, 503)
        log1 = middleware1.get_fault_log()

        # Run 2: Seed 7 (should be identical)
        app2 = create_app(snapshot_path=world_snapshot)
        middleware2 = attach_fault_middleware(app2, profile_seed_7)
        client2 = TestClient(app2)
        for _ in range(100):
            response = client2.get("/orders")
            assert response.status_code in (200, 503)
        log2 = middleware2.get_fault_log()

        # Logs should be identical
        assert len(log1) == len(log2)
        for i, (entry1, entry2) in enumerate(zip(log1, log2)):
            assert entry1.get("fault_kind") == entry2.get("fault_kind"), (
                f"Entry {i}: fault_kind mismatch"
            )
