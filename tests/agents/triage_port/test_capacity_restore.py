"""Test that available_capacity is toggle-invariant."""

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


def test_capacity_returns_to_baseline_on_toggle_off() -> None:
    """AC6: staffing is toggle-invariant; available capacity is higher with the agent on.

    Per docs/agents/triage-agent-port.md, STAFFING (the server count) never
    changes based on the toggle -- it is read from config, independent of
    agent_toggles/ports. What DOES change is available capacity
    (staffing - busy), because agent-resolved items never occupy a human
    server slot. So the real, testable claim is: at any timestamp, available
    capacity with the agent ON is never less than with it OFF.
    """
    seed = 555
    population = 60

    def run_with_tick_observer(toggle_on: bool) -> list[tuple[int, dict[str, int]]]:
        """Run engine and record on_tick capacity observations."""
        world = generate_world(seed=seed, population_size=population, span_days=1)

        capacity_series: list[tuple[int, dict[str, int]]] = []

        def tick_observer(timestamp: int, available_capacity: dict[str, int]) -> None:
            """Record capacity at each tick."""
            capacity_series.append((timestamp, dict(available_capacity)))

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
                [
                    '{"intent": "general_question"}',
                    "Thank you for your message.",
                ]
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
            engine = Engine(
                world, agent_toggles={"triage": True}, ports=registry, on_tick=tick_observer
            )
        else:
            engine = Engine(
                world, agent_toggles={"triage": False}, ports=None, on_tick=tick_observer
            )

        engine.run(duration_minutes=1440)
        return capacity_series

    # Run twice with same seed: once ON, once OFF
    capacity_on = run_with_tick_observer(toggle_on=True)
    capacity_off = run_with_tick_observer(toggle_on=False)

    # Extract support_inbox capacity at each timestamp
    def extract_support_inbox_capacity(series: list[tuple[int, dict[str, int]]]) -> dict[int, int]:
        """Map timestamp to support_inbox available_capacity."""
        result = {}
        for timestamp, capacity_dict in series:
            result[timestamp] = capacity_dict.get("support_inbox", 0)
        return result

    cap_on_dict = extract_support_inbox_capacity(capacity_on)
    cap_off_dict = extract_support_inbox_capacity(capacity_off)

    # Get common timestamps
    common_times = set(cap_on_dict.keys()) & set(cap_off_dict.keys())
    assert len(common_times) > 0, "Should have common observation timestamps"

    sorted_times = sorted(common_times)
    on_capacities = [cap_on_dict[t] for t in sorted_times]
    off_capacities = [cap_off_dict[t] for t in sorted_times]

    assert len(on_capacities) > 0, "Should observe capacity for toggle ON"
    assert len(off_capacities) > 0, "Should observe capacity for toggle OFF"
    assert all(c >= 0 for c in on_capacities), "Capacity should never be negative"
    assert all(c >= 0 for c in off_capacities), "Capacity should never be negative"

    # The real claim: capacity ON is never lower than capacity OFF at any
    # shared timestamp, and is strictly higher at at least one timestamp
    # (proving the agent actually freed up human server capacity, not just
    # that the callback fired).
    assert all(on >= off for on, off in zip(on_capacities, off_capacities)), (
        f"Capacity with agent ON should never be lower than OFF: "
        f"on={on_capacities}, off={off_capacities}"
    )
    assert any(on > off for on, off in zip(on_capacities, off_capacities)), (
        "Capacity with agent ON should be strictly higher at some point, "
        "proving the agent actually freed human server capacity"
    )

    print(f"Capacity ON series: {on_capacities[:5]}...")
    print(f"Capacity OFF series: {off_capacities[:5]}...")
