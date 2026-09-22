"""Test that guard_final sits between human_approval and send.

AC5: guard_final is wired between the gate and send: given a HumanDecision of edit whose
text is an expected-block corpus case, the run ends at human_review carrying that case's
rule id in the reason field and the spy OutboundPort records zero send calls; the same run
with unedited allowed text ends at send with exactly one recorded call.
"""

import sqlite3
from datetime import datetime
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
from clinicloop.evals.guard.corpus_loader import load_cases
from clinicloop.hitl.decision import HumanDecision

SERDE = JsonPlusSerializer(allowed_msgpack_modules=TRIAGE_ALLOWED_MSGPACK_MODULES)


class InstantToolRunner:
    """Returns a fixed summary immediately (unused for general_question, kept for parity)."""

    def run(self, name: str, patient_id: str, order_id: str | None) -> str:
        """Return a fixed summary."""
        return f"Order {order_id} is in transit"


def _real_block_case_text() -> tuple[str, str]:
    """A real expected-block corpus case's assistant text and its rule id."""
    case = next(c for c in load_cases() if c.expected_verdict == "block")
    text = next(m.text for m in case.thread if m.role == "assistant")
    assert case.expected_rule_id is not None
    return text, case.expected_rule_id


def _build(tmp_path: Path, name: str, allowed_draft: str, spy: list[str]) -> tuple[Any, Any]:
    """Build a graph up to human_approval for a general_question case (no tool call needed)."""
    message_source = InMemoryMessageSource({"msg-001": "Do you accept PayPal?"})
    model = FakeModelPort(['{"intent": "general_question"}', allowed_draft])
    ruleset = load_ruleset("au")
    conn = sqlite3.connect(str(tmp_path / f"{name}.sqlite"), check_same_thread=False)
    compiled = build_triage_graph(
        model=model,
        tools=InstantToolRunner(),
        ruleset=ruleset,
        message_source=message_source,
        outbound_port=OutboundPort(spy.append, ruleset),
        run_key="test",
        checkpointer=SqliteSaver(conn, serde=SERDE),
    )
    return compiled, conn


def test_human_edit_to_a_blocked_case_routes_to_human_review(tmp_path: Path) -> None:
    """AC5 (block path): an approved-looking draft edited to a real block case is caught."""
    blocked_text, expected_rule_id = _real_block_case_text()
    spy: list[str] = []
    compiled, conn = _build(tmp_path, "block", "Your order is being processed.", spy)

    config = {"configurable": {"thread_id": "case-block", "message_id": "msg-001"}}
    compiled.invoke({"case_id": "case-block", "patient_id": "P-001"}, config)
    assert compiled.get_state(config).next == ("human_approval",)

    compiled.update_state(
        config,
        {
            "human_decision": HumanDecision(
                action="edit",
                decided_by="clinician-001",
                decided_at=datetime.now(),
                edited_text=blocked_text,
            )
        },
    )
    final = compiled.invoke(None, config)

    assert final.get("routing_reason") == "rule_block"
    assert expected_rule_id in final.get("routing_rule_ids", ())
    assert compiled.get_state(config).next == ()
    assert len(spy) == 0
    conn.close()


def test_human_approval_of_the_original_draft_reaches_send(tmp_path: Path) -> None:
    """AC5 (allow path): approving the original, unedited allowed draft reaches send once."""
    allowed_text = "Yes, we accept PayPal for all orders."
    spy: list[str] = []
    compiled, conn = _build(tmp_path, "allow", allowed_text, spy)

    config = {"configurable": {"thread_id": "case-allow", "message_id": "msg-001"}}
    compiled.invoke({"case_id": "case-allow", "patient_id": "P-001"}, config)
    assert compiled.get_state(config).next == ("human_approval",)

    compiled.update_state(
        config,
        {
            "human_decision": HumanDecision(
                action="approve",
                decided_by="clinician-001",
                decided_at=datetime.now(),
            )
        },
    )
    final = compiled.invoke(None, config)

    assert final.get("routing_reason") is None
    assert final["guard_verdicts"][-1].allowed is True
    assert compiled.get_state(config).next == ()
    assert len(spy) == 1
    assert spy[0] == allowed_text
    conn.close()
