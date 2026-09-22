"""Test that escalated/blocked cases route to the human queue without loss."""

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
from clinicloop.world.entities.models import Message
from clinicloop.world.generator import generate_world
from clinicloop.world.ports.registry import PortRegistry


class InstantToolRunner:
    """Returns a fixed summary immediately."""

    def run(self, name: str, patient_id: str, order_id: str | None) -> str:
        """Return a fixed summary."""
        return f"Order {order_id} is in transit"


def _checkpointer_factory() -> SqliteSaver:
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    return SqliteSaver(
        conn, serde=JsonPlusSerializer(allowed_msgpack_modules=TRIAGE_ALLOWED_MSGPACK_MODULES)
    )


def test_escalated_case_reaches_human_queue_without_loss() -> None:
    """AC4: a case the port escalates still gets a real record; it is not dropped.

    The synthetic corpus never naturally generates a distress message (verified
    empirically: 0/100 messages trigger escalation across seeds 1-5 at
    population=200), so this injects one real, hand-crafted `Message` with
    genuine escalation-triggering text into an otherwise normally generated world.
    """
    seed = 789
    world = generate_world(seed=seed, population_size=50, span_days=1)

    forced_message = Message(
        message_id="forced-distress-0001",
        patient_id=world.messages[0].patient_id if world.messages else "patient-0001",
        channel="chat",
        received_at_minute=60,
        body="I'm having thoughts of suicide. I can't handle this anymore.",
        synthetic=True,
    )
    world = world._replace(messages=[*world.messages, forced_message])

    model = FakeModelPort(['{"intent": "general_question"}', "Thank you for your message."] * 60)
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
        checkpointer_factory=_checkpointer_factory,
    )

    registry = PortRegistry()
    registry.register("triage", port)
    engine = Engine(world, agent_toggles={"triage": True}, ports=registry)
    result = engine.run(duration_minutes=1440)

    # Not lost: the forced message still has a real support_inbox record.
    matching_records = [
        r
        for r in result.records
        if r.queue == "support_inbox" and r.item_id == "forced-distress-0001"
    ]
    assert len(matching_records) == 1, "The escalated case must produce exactly one record"
    assert matching_records[0].finished_at is not None, "The escalated case must still finish"

    # Routed to the human queue: a PortFailure was recorded for CaseEscalated,
    # and a human server (not the agent) resolved it.
    escalation_failures = [
        pf for pf in result.port_failures if pf.exception_type == "CaseEscalated"
    ]
    assert len(escalation_failures) == 1, (
        f"Expected exactly one CaseEscalated PortFailure, got {result.port_failures}"
    )
    assert matching_records[0].server is not None, (
        "An escalated case must be served by a human worker, not the agent"
    )

    # Confirm the adapter itself recorded the distress case as escalated.
    forced_record = next(r for r in port.service_log if r.case_id == "forced-distress-0001")
    assert forced_record.outcome == "escalated"
