"""Test that TriageAgentPort produces deterministic runs."""

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


def test_same_seed_and_toggle_give_identical_run_hash() -> None:
    """AC3: Two runs at the same seed and toggle state produce identical run_hash."""
    seed = 456
    population = 50

    def run_simulation(toggle_on: bool) -> str:
        """Run a simulation and return its run_hash."""
        world = generate_world(seed=seed, population_size=population, span_days=1)

        if toggle_on:

            def checkpointer_factory() -> SqliteSaver:
                conn = sqlite3.connect(":memory:", check_same_thread=False)
                return SqliteSaver(
                    conn,
                    serde=JsonPlusSerializer(
                        allowed_msgpack_modules=TRIAGE_ALLOWED_MSGPACK_MODULES
                    ),
                )

            model = FakeModelPort(
                ['{"intent": "general_question"}', "Thank you for your message."] * 50
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
        else:
            engine = Engine(world, agent_toggles={"triage": False}, ports=None)

        result = engine.run(duration_minutes=1440)
        return result.run_hash

    # Run twice with toggle ON
    hash_on_a = run_simulation(toggle_on=True)
    hash_on_b = run_simulation(toggle_on=True)

    # Run twice with toggle OFF
    hash_off_a = run_simulation(toggle_on=False)
    hash_off_b = run_simulation(toggle_on=False)

    # Assert determinism
    assert hash_on_a == hash_on_b, "Two ON runs should produce identical hashes"
    assert hash_off_a == hash_off_b, "Two OFF runs should produce identical hashes"
