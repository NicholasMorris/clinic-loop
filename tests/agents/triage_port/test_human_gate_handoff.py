"""Test that paused cases return to the human queue."""

import sqlite3

import pytest
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from langgraph.checkpoint.sqlite import SqliteSaver

from clinicloop.agents.triage.graph.builder import (
    TRIAGE_ALLOWED_MSGPACK_MODULES,
)
from clinicloop.agents.triage.models import FakeModelPort
from clinicloop.agents.triage.ports.agent_port import TriageAgentPort
from clinicloop.agents.triage.ports.exceptions import CaseEscalated
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


def test_paused_case_returns_to_human_queue() -> None:
    """AC4: A case that escalates raises CaseEscalated and falls back to human pool."""
    seed = 789
    world = generate_world(seed=seed, population_size=15, span_days=1)

    def checkpointer_factory() -> SqliteSaver:
        conn = sqlite3.connect(":memory:", check_same_thread=False)
        return SqliteSaver(
            conn, serde=JsonPlusSerializer(allowed_msgpack_modules=TRIAGE_ALLOWED_MSGPACK_MODULES)
        )

    # A message containing an adverse event will escalate
    # Use a scripted model to force escalation
    model = FakeModelPort(
        ['{"intent": "adverse_event"}', "This case has been escalated."]
        * 50
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
    engine = Engine(world, agent_toggles={"triage": True}, ports=registry)
    result = engine.run(duration_minutes=1440)

    # Check that some cases escalated and returned to human queue
    # The port_failures list should contain CaseEscalated exceptions
    escalation_failures = [
        pf for pf in result.port_failures if pf.exception_type == "CaseEscalated"
    ]

    # Some cases should have escalated
    assert len(escalation_failures) > 0, "At least one case should have escalated"

    # For each escalated case, verify it's in the records with a human server
    for failure in escalation_failures:
        case_records = [r for r in result.records if r.item_id == failure.case_id]
        assert len(case_records) > 0, f"Escalated case {failure.case_id} should be in records"

        # The case should have started service (human pool picked it up)
        record = case_records[0]
        if record.started_at is not None:
            assert record.server is not None, "Human-served case should have a server_id"

    print(f"Escalation failures: {len(escalation_failures)}")
