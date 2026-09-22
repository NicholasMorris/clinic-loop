"""Test that TriageAgentPort implements the AgentPort protocol."""

import sqlite3
from pathlib import Path

from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from langgraph.checkpoint.sqlite import SqliteSaver

from clinicloop.agents.triage.graph.builder import (
    TRIAGE_ALLOWED_MSGPACK_MODULES,
)
from clinicloop.agents.triage.models import FakeModelPort
from clinicloop.agents.triage.ports.agent_port import TriageAgentPort
from clinicloop.compliance.outbound.port import OutboundPort
from clinicloop.compliance.rulesets import load_ruleset
from clinicloop.world.generator import generate_world
from clinicloop.world.ports.protocol import AgentPort


class InstantToolRunner:
    """Returns a fixed summary immediately."""

    def run(self, name: str, patient_id: str, order_id: str | None) -> str:
        """Return a fixed summary."""
        return f"Order {order_id} is in transit"


def test_adapter_satisfies_agent_port_protocol(tmp_path: Path) -> None:
    """AC1: isinstance check passes and serve() returns a float."""
    # Build a small fixture world
    world = generate_world(seed=42, population_size=10, span_days=1)

    # Create the port with a scripted model that returns a general_question
    # and an approved draft
    def checkpointer_factory() -> SqliteSaver:
        """Create a fresh checkpointer for each case."""
        conn = sqlite3.connect(":memory:", check_same_thread=False)
        return SqliteSaver(
            conn, serde=JsonPlusSerializer(allowed_msgpack_modules=TRIAGE_ALLOWED_MSGPACK_MODULES)
        )

    model = FakeModelPort(
        [
            '{"intent": "general_question"}',
            "Your message has been received and will be reviewed.",
        ]
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

    # Check protocol
    assert isinstance(port, AgentPort), "TriageAgentPort should implement AgentPort protocol"

    # Find a support_inbox message to serve
    if world.messages:
        message = world.messages[0]
        # Serve the case
        service_minutes = port.serve(message.message_id)

        # Should return a float
        assert isinstance(service_minutes, float), (
            f"serve() should return float, got {type(service_minutes)}"
        )
        assert service_minutes >= 0, f"service_minutes should be >= 0, got {service_minutes}"
