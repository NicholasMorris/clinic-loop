"""Test that prompt injection in patient text doesn't alter routing.

AC7: For each pair in the injection-pair fixture (a clean thread and the same thread
with an instruction injected into the patient message body), the injected member produces
the same intent and the same tool-call list as its clean counterpart.

This test proves the tool-binding invariant survives graph assembly, using scripted
FakeModelPort responses for determinism. Separate real evidence that the live model
correctly classifies prompt-injection attempts already exists in M2-5a's
recorded_intent.jsonl (5 real prompt_injection-labelled recordings); it is not
re-recorded here.
"""

import sqlite3
from pathlib import Path
from typing import Any

from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from langgraph.checkpoint.sqlite import SqliteSaver

from clinicloop.agents.triage.graph.builder import (
    TRIAGE_ALLOWED_MSGPACK_MODULES,
    build_triage_graph,
)
from clinicloop.agents.triage.graph.message_source import InMemoryMessageSource
from clinicloop.agents.triage.models import FakeModelPort
from clinicloop.compliance.outbound.port import OutboundPort
from clinicloop.compliance.rulesets import load_ruleset

SERDE = JsonPlusSerializer(allowed_msgpack_modules=TRIAGE_ALLOWED_MSGPACK_MODULES)
TOOL_INTENTS = {"order_status", "cancellation", "delivery_problem"}


class InstantToolRunner:
    """Returns a fixed summary immediately, independent of the (ignored) model args."""

    def run(self, name: str, patient_id: str, order_id: str | None) -> str:
        """Return a fixed summary, independent of the (ignored) model args."""
        return f"Order {order_id} status for {patient_id}"


def _run(
    tmp_path: Path, name: str, text: str, expected_intent: str, expected_tool: str | None
) -> dict[str, Any]:
    """Run one thread through the graph up to the human_approval pause."""
    responses = [f'{{"intent": "{expected_intent}"}}']
    if expected_intent in TOOL_INTENTS:
        responses.append(f'{{"tool": "{expected_tool}", "args": {{}}}}')
    # The graph runs the whole happy path up to the human_approval pause, so draft's
    # model call needs a scripted response too even though this test only checks
    # intent and tool_calls, both of which are already fixed before draft runs.
    responses.append("Thanks, I can help with that.")
    model = FakeModelPort(responses)

    message_source = InMemoryMessageSource({"msg": text})
    ruleset = load_ruleset("au")
    conn = sqlite3.connect(str(tmp_path / f"{name}.sqlite"), check_same_thread=False)
    compiled = build_triage_graph(
        model=model,
        tools=InstantToolRunner(),
        ruleset=ruleset,
        message_source=message_source,
        outbound_port=OutboundPort(lambda text: None, ruleset),
        run_key="test",
        checkpointer=SqliteSaver(conn, serde=SERDE),
    )
    config = {"configurable": {"thread_id": name, "message_id": "msg"}}
    final = compiled.invoke({"case_id": name, "patient_id": "P-001"}, config)
    conn.close()
    return dict(final)


def test_instructions_inside_patient_text_do_not_alter_routing(
    injection_pairs: list[dict[str, str]], tmp_path: Path
) -> None:
    """AC7: every pair's injected thread yields the same intent and tool calls as clean."""
    assert injection_pairs, "injection_pairs fixture must not be empty"

    for pair in injection_pairs:
        pair_id = pair["pair_id"]
        expected_intent = pair["expected_intent"]
        expected_tool = pair.get("expected_tool")

        clean = _run(tmp_path, f"clean-{pair_id}", pair["clean"], expected_intent, expected_tool)
        injected = _run(
            tmp_path, f"injected-{pair_id}", pair["injected"], expected_intent, expected_tool
        )

        assert clean["intent"] == injected["intent"] == expected_intent, pair_id
        clean_calls = [(c.name, c.args) for c in clean.get("tool_calls", [])]
        injected_calls = [(c.name, c.args) for c in injected.get("tool_calls", [])]
        assert clean_calls == injected_calls, pair_id
        if expected_intent in TOOL_INTENTS:
            assert clean_calls == [(expected_tool, {"patient_id": "P-001", "order_id": ""})]
