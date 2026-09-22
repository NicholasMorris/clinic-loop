"""Test that toggling the triage agent off increases queue depth."""

import sqlite3
from pathlib import Path

import pytest
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from langgraph.checkpoint.sqlite import SqliteSaver

from clinicloop.agents.triage.graph.builder import (
    TRIAGE_ALLOWED_MSGPACK_MODULES,
)
from clinicloop.agents.triage.models import FakeModelPort
from clinicloop.agents.triage.ports.agent_port import TriageAgentPort
from clinicloop.compliance.outbound.port import OutboundPort
from clinicloop.compliance.rulesets import load_ruleset
from clinicloop.world.engine.loop import Engine
from clinicloop.world.generator import generate_world
from clinicloop.world.ports.registry import PortRegistry


class InstantToolRunner:
    """Returns a fixed summary immediately."""

    def run(self, name: str, patient_id: str, order_id: str | None) -> str:
        """Return a fixed summary."""
        return f"Order {order_id} is in transit"


def test_inbox_depth_and_median_wait_rise_when_agent_is_off(tmp_path: Path) -> None:
    """AC2: support_inbox depth and median wait are strictly greater when agent is off."""
    seed = 123
    population = 30

    # Create two worlds with the same seed for comparison
    world_on = generate_world(seed=seed, population_size=population, span_days=1)
    world_off = generate_world(seed=seed, population_size=population, span_days=1)

    def make_port(world: any) -> PortRegistry:
        """Create a PortRegistry with a registered TriageAgentPort."""

        def checkpointer_factory() -> SqliteSaver:
            conn = sqlite3.connect(":memory:", check_same_thread=False)
            return SqliteSaver(
                conn, serde=JsonPlusSerializer(allowed_msgpack_modules=TRIAGE_ALLOWED_MSGPACK_MODULES)
            )

        model = FakeModelPort(
            ['{"intent": "general_question"}', "Thank you for your message."]
            * 50  # Enough responses for all messages
        )
        ruleset = load_ruleset("au")
        sent_texts: list[str] = []
        outbound = OutboundPort(sent_texts.append, ruleset)

        port = TriageAgentPort(
            world=world,
            model=model,
            tools=InstantToolRunner(),
            ruleset=ruleset,
            outbound_port=outbound,
            classifier=None,
            checkpointer_factory=checkpointer_factory,
        )

        registry = PortRegistry()
        registry.register("triage", port)
        return registry

    # Run with agent ON
    registry_on = make_port(world_on)
    engine_on = Engine(world_on, agent_toggles={"triage": True}, ports=registry_on)
    result_on = engine_on.run(duration_minutes=1440)

    # Run with agent OFF
    engine_off = Engine(world_off, agent_toggles={"triage": False}, ports=None)
    result_off = engine_off.run(duration_minutes=1440)

    # Extract queue depths for support_inbox
    depths_on = [depth for _, depth in result_on.queue_depth["support_inbox"]]
    depths_off = [depth for _, depth in result_off.queue_depth["support_inbox"]]

    max_depth_on = max(depths_on) if depths_on else 0
    max_depth_off = max(depths_off) if depths_off else 0

    # Compute median wait from queue records
    def compute_median_wait(result: any, queue: str) -> float:
        """Compute median wait time for a queue."""
        waits = []
        for record in result.records:
            if record.queue == queue and record.started_at is not None:
                wait = record.started_at - record.enqueued_at
                waits.append(wait)
        if not waits:
            return 0.0
        waits.sort()
        return float(waits[len(waits) // 2])

    median_wait_on = compute_median_wait(result_on, "support_inbox")
    median_wait_off = compute_median_wait(result_off, "support_inbox")

    # Assert that OFF > ON
    assert (
        max_depth_off > max_depth_on
    ), f"Max depth off ({max_depth_off}) should be > on ({max_depth_on})"
    assert (
        median_wait_off > median_wait_on
    ), f"Median wait off ({median_wait_off}) should be > on ({median_wait_on})"

    print(f"Agent ON  - Max depth: {max_depth_on}, Median wait: {median_wait_on}")
    print(f"Agent OFF - Max depth: {max_depth_off}, Median wait: {median_wait_off}")
