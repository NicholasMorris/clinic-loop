"""Test that available_capacity is toggle-invariant."""

import sqlite3

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


def test_capacity_returns_to_baseline_on_toggle_off() -> None:
    """AC6: available_capacity is toggle-invariant; capacity never changes, only demand does."""
    seed = 555
    population = 25

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
                    conn, serde=JsonPlusSerializer(allowed_msgpack_modules=TRIAGE_ALLOWED_MSGPACK_MODULES)
                )

            model = FakeModelPort(
                ['{"intent": "general_question"}', "Thank you for your message."]
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
            engine = Engine(world, agent_toggles={"triage": True}, ports=registry, on_tick=tick_observer)
        else:
            engine = Engine(world, agent_toggles={"triage": False}, ports=None, on_tick=tick_observer)

        result = engine.run(duration_minutes=1440)
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

    # Assert capacity is identical at every common timestamp
    for timestamp in sorted(common_times):
        cap_on = cap_on_dict[timestamp]
        cap_off = cap_off_dict[timestamp]
        assert (
            cap_on == cap_off
        ), f"At time {timestamp}: capacity should be invariant, but got ON={cap_on}, OFF={cap_off}"

    print(f"Capacity ON series: {sorted(cap_on_dict.items())[:5]}...")
    print(f"Capacity OFF series: {sorted(cap_off_dict.items())[:5]}...")
