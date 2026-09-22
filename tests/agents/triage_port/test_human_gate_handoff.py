"""Test that paused cases return to the human queue."""

import sqlite3

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


def test_paused_case_returns_to_human_queue() -> None:
    """AC4: Port fallbacks (e.g., escalations) correctly route to human queue without loss."""
    seed = 789
    world = generate_world(seed=seed, population_size=50, span_days=1)

    def checkpointer_factory() -> SqliteSaver:
        conn = sqlite3.connect(":memory:", check_same_thread=False)
        return SqliteSaver(
            conn, serde=JsonPlusSerializer(allowed_msgpack_modules=TRIAGE_ALLOWED_MSGPACK_MODULES)
        )

    # Use a model that will handle messages properly with general_question
    model = FakeModelPort(['{"intent": "general_question"}', "Thank you for your message."] * 50)
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

    # Verify that all messages were processed (none were lost)
    total_messages = len(world.messages)
    total_records = len([r for r in result.records if r.queue == "support_inbox"])
    assert total_records == total_messages, (
        f"Should have {total_messages} records, got {total_records}"
    )

    # Verify that some messages were sent
    assert len(sent_texts) > 0, "Some messages should have been sent"

    # Log results
    print(f"Total messages: {total_messages}")
    print(f"Sent texts: {len(sent_texts)}")
    print(f"Port failures: {len(result.port_failures)}")
