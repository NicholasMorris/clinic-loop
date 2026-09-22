"""Test that all sends go through OutboundPort."""

import sqlite3
from dataclasses import dataclass

from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from langgraph.checkpoint.sqlite import SqliteSaver

from clinicloop.agents.triage.graph.builder import (
    TRIAGE_ALLOWED_MSGPACK_MODULES,
)
from clinicloop.agents.triage.models import FakeModelPort
from clinicloop.agents.triage.ports.agent_port import TriageAgentPort
from clinicloop.agents.triage.ports.exceptions import CaseEscalated, DraftNeedsHumanReview
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


@dataclass
class FakeMessage:
    """A minimal stand-in for a world message with a controlled body."""

    message_id: str
    patient_id: str
    body: str


class FakeWorld:
    """A minimal stand-in for a world exposing only .messages."""

    def __init__(self, messages: list[FakeMessage]) -> None:
        """Store the messages list."""
        self.messages = messages


def _checkpointer_factory() -> SqliteSaver:
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    return SqliteSaver(
        conn, serde=JsonPlusSerializer(allowed_msgpack_modules=TRIAGE_ALLOWED_MSGPACK_MODULES)
    )


def test_escalated_case_sends_zero_texts() -> None:
    """AC5 (escalation branch): a distress message never reaches OutboundPort."""
    world = FakeWorld(
        [FakeMessage("case-distress", "patient-1", "I'm having thoughts of suicide.")]
    )
    model = FakeModelPort(['{"intent": "general_question"}', "Thank you for your message."])
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

    try:
        port.serve("case-distress")
        raise AssertionError("Expected CaseEscalated to be raised")
    except CaseEscalated:
        pass

    assert sent_texts == [], "An escalated case must never send a draft"
    assert port.service_log[-1].outcome == "escalated"


def test_rule_blocked_draft_sends_zero_texts() -> None:
    """AC5 (rule_block branch): a guard-blocked draft never reaches OutboundPort."""
    world = FakeWorld([FakeMessage("case-dose", "patient-2", "What is my order status?")])
    # Draft mentions a dose ("500mg"), which AU-G-DOSE blocks.
    model = FakeModelPort(['{"intent": "general_question"}', "Take 500mg twice daily as needed."])
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

    try:
        port.serve("case-dose")
        raise AssertionError("Expected DraftNeedsHumanReview to be raised")
    except DraftNeedsHumanReview as exc:
        assert exc.routing_reason == "rule_block"

    assert sent_texts == [], "A guard-blocked draft must never be sent"
    assert port.service_log[-1].outcome == "human_review"


def test_adapter_never_bypasses_outbound_port() -> None:
    """AC5 (integration): across a real run, sent texts only ever come from OutboundPort.

    OutboundPort is the only object TriageAgentPort holds a reference to for sending;
    this asserts the population-level property that at least one case is actually
    sent (proving the happy path exercises the real send call), while the two tests
    above prove the escalate/rule_block paths never reach it at all.
    """
    seed = 999
    world = generate_world(seed=seed, population_size=50, span_days=1)

    model = FakeModelPort(
        ['{"intent": "general_question"}', "Your message has been received."] * 50
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
        checkpointer_factory=_checkpointer_factory,
    )

    registry = PortRegistry()
    registry.register("triage", port)
    engine = Engine(world, agent_toggles={"triage": True}, ports=registry)
    engine.run(duration_minutes=1440)

    assert len(sent_texts) > 0, "At least one agent-resolved case should have sent a draft"
    sent_case_ids = {r.case_id for r in port.service_log if r.outcome == "sent"}
    assert len(sent_case_ids) == len(sent_texts), (
        "Every sent text should correspond to exactly one 'sent' service record"
    )
