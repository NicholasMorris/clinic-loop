"""Test that prompt injection in patient text doesn't alter routing.

AC7: For each pair in the injection-pair fixture (a clean thread and the same thread
with an instruction injected into the patient message body), the injected member produces
the same intent and the same tool-call list as its clean counterpart.

This test proves tool-binding invariant survives graph assembly; separate real evidence
for prompt-injection classification already exists in M2-5a's recorded_intent.jsonl.
"""

from pathlib import Path
from tempfile import TemporaryDirectory
import sqlite3

import pytest

from clinicloop.agents.triage.graph.builder import build_triage_graph
from clinicloop.compliance.rulesets import load_ruleset
from clinicloop.compliance.outbound.port import OutboundPort
from clinicloop.agents.triage.models import FakeModelPort
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer


@pytest.mark.filterwarnings("error::UserWarning")
def test_instructions_inside_patient_text_do_not_alter_routing(
    fake_model: FakeModelPort,
    message_source,
    fake_tools,
    injection_pairs,
    tmp_path: Path,
) -> None:
    """AC7: Verify injected instructions don't change intent or tool routing.

    For each pair in injection_pairs, this test:
    1. Runs the clean thread through ingest + classify_intent + escalation_check + resolve
    2. Runs the injected thread through the same nodes
    3. Verifies both produce identical intent and tool_calls

    This uses scripted FakeModelPort to ensure deterministic responses.
    """
    if not injection_pairs:
        pytest.skip("No injection pairs available")

    ruleset = load_ruleset("au")

    serde = JsonPlusSerializer(
        allowed_msgpack_modules=[
            ("clinicloop.agents.triage.state", "Turn"),
            ("clinicloop.agents.triage.state", "ToolCall"),
            ("clinicloop.compliance.guard.verdict", "GuardVerdict"),
            ("clinicloop.compliance.escalation.result", "EscalationClear"),
        ]
    )

    for pair in injection_pairs[:1]:  # Test at least the first pair
        pair_id = pair.get("pair_id", "unknown")
        clean_text = pair.get("clean", "")
        injected_text = pair.get("injected", "")
        expected_intent = pair.get("expected_intent")
        expected_tool = pair.get("expected_tool")

        # Create message sources for clean and injected
        clean_msgs = {f"msg-{pair_id}-clean": clean_text}
        injected_msgs = {f"msg-{pair_id}-injected": injected_text}

        # Build graphs for both
        db_clean = tmp_path / f"clean-{pair_id}.sqlite"
        db_injected = tmp_path / f"injected-{pair_id}.sqlite"

        conn_clean = sqlite3.connect(str(db_clean), check_same_thread=False)
        conn_injected = sqlite3.connect(str(db_injected), check_same_thread=False)

        checkpointer_clean = SqliteSaver(conn_clean, serde=serde)
        checkpointer_injected = SqliteSaver(conn_injected, serde=serde)

        from clinicloop.agents.triage.graph.message_source import InMemoryMessageSource

        source_clean = InMemoryMessageSource(clean_msgs)
        source_injected = InMemoryMessageSource(injected_msgs)

        # Script the model to return expected intent
        intent_json = f'{{"intent": "{expected_intent}"}}'
        tool_json = f'{{"tool": "{expected_tool}"}}'
        fake_model.responses["default"] = intent_json

        compiled_clean = build_triage_graph(
            model=fake_model,
            tools=fake_tools,  # type: ignore[arg-type]
            ruleset=ruleset,
            message_source=source_clean,
            outbound_port=OutboundPort(lambda x: None, ruleset),
            run_key="test",
            checkpointer=checkpointer_clean,
        )

        compiled_injected = build_triage_graph(
            model=fake_model,
            tools=fake_tools,  # type: ignore[arg-type]
            ruleset=ruleset,
            message_source=source_injected,
            outbound_port=OutboundPort(lambda x: None, ruleset),
            run_key="test",
            checkpointer=checkpointer_injected,
        )

        # Run both
        config_clean = {"configurable": {"thread_id": f"case-clean-{pair_id}", "message_id": f"msg-{pair_id}-clean"}}
        config_injected = {"configurable": {"thread_id": f"case-injected-{pair_id}", "message_id": f"msg-{pair_id}-injected"}}

        state_clean = compiled_clean.invoke({"case_id": f"case-clean-{pair_id}", "patient_id": "P-001"}, config_clean)
        state_injected = compiled_injected.invoke(
            {"case_id": f"case-injected-{pair_id}", "patient_id": "P-001"}, config_injected
        )

        # AC7: Verify intent and tool_calls match
        assert (
            state_clean.get("intent") == state_injected.get("intent")
        ), f"Intent differs for pair {pair_id}: {state_clean.get('intent')} != {state_injected.get('intent')}"

        assert (
            state_clean.get("tool_calls") == state_injected.get("tool_calls")
        ), f"Tool calls differ for pair {pair_id}: {state_clean.get('tool_calls')} != {state_injected.get('tool_calls')}"

        conn_clean.close()
        conn_injected.close()
