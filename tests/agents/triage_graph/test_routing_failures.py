"""Test routing of different failure cases.

AC6: Routing failures land on the documented terminals:
- non-English inbound fixture ends at human_review with reason "language"
- blocked draft ends at human_review with reason "rule_block" and the rule id
- escalated case ends at escalate carrying its escalation_category
- tool call raising a timeout ends at escalate with reason "tool_timeout"
"""

import sqlite3
import time
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


class InstantToolRunner:
    """Returns a fixed summary immediately."""

    def run(self, name: str, patient_id: str, order_id: str | None) -> str:
        """Return a fixed summary."""
        return f"Order {order_id} is in transit"


class SlowToolRunner:
    """Sleeps past any reasonable timeout before returning."""

    def run(self, name: str, patient_id: str, order_id: str | None) -> str:
        """Sleep past any reasonable timeout, then return."""
        time.sleep(2.0)
        return "should never be reached"


def _build(
    tmp_path: Path, name: str, model: FakeModelPort, tools: Any, message_source: Any, spy: list[str]
) -> tuple[Any, Any]:
    conn = sqlite3.connect(str(tmp_path / f"{name}.sqlite"), check_same_thread=False)
    ruleset = load_ruleset("au")
    compiled = build_triage_graph(
        model=model,
        tools=tools,
        ruleset=ruleset,
        message_source=message_source,
        outbound_port=OutboundPort(spy.append, ruleset),
        run_key="test",
        timeout_seconds=0.2,
        checkpointer=SqliteSaver(conn, serde=SERDE),
    )
    return compiled, conn


def test_non_english_message_ends_at_human_review_with_language_reason(tmp_path: Path) -> None:
    """AC6 case 1: a non-English inbound message routes to human_review, reason 'language'."""
    message_source = InMemoryMessageSource({"msg-es": "¿Cuándo llega mi pedido?"})
    model = FakeModelPort(['{"intent": "general_question"}'])
    spy: list[str] = []
    compiled, conn = _build(tmp_path, "language", model, InstantToolRunner(), message_source, spy)

    config = {"configurable": {"thread_id": "case-lang", "message_id": "msg-es"}}
    final = compiled.invoke({"case_id": "case-lang", "patient_id": "P-001"}, config)

    assert final.get("routing_reason") == "language"
    assert final.get("draft") is None
    assert compiled.get_state(config).next == ()
    assert len(spy) == 0
    conn.close()


def test_blocked_draft_ends_at_human_review_with_rule_block_reason(tmp_path: Path) -> None:
    """AC6 case 2: a draft the guard blocks routes to human_review, reason 'rule_block'."""
    message_source = InMemoryMessageSource({"msg-block": "Can you help with my prescriptions?"})
    model = FakeModelPort(
        [
            '{"intent": "general_question"}',
            "Take veltrazine tonight.",
        ]
    )
    spy: list[str] = []
    compiled, conn = _build(tmp_path, "blocked", model, InstantToolRunner(), message_source, spy)

    config = {"configurable": {"thread_id": "case-block", "message_id": "msg-block"}}
    final = compiled.invoke({"case_id": "case-block", "patient_id": "P-001"}, config)

    assert final.get("routing_reason") == "rule_block"
    assert "AU-G-PRODUCT" in final.get("routing_rule_ids", ())
    assert compiled.get_state(config).next == ()
    assert len(spy) == 0
    conn.close()


def test_escalating_message_ends_at_escalate_with_category(tmp_path: Path) -> None:
    """AC6 case 3: a distress message routes to escalate, carrying its category."""
    message_source = InMemoryMessageSource(
        {"msg-distress": "I want to end my life, I can't go on."}
    )
    model = FakeModelPort(['{"intent": "mental_health_distress"}'])
    spy: list[str] = []
    compiled, conn = _build(tmp_path, "escalate", model, InstantToolRunner(), message_source, spy)

    config = {"configurable": {"thread_id": "case-escalate", "message_id": "msg-distress"}}
    final = compiled.invoke({"case_id": "case-escalate", "patient_id": "P-001"}, config)

    assert final.get("escalation_category") == "distress"
    assert compiled.get_state(config).next == ()
    assert len(spy) == 0
    conn.close()


def test_tool_timeout_ends_at_escalate_with_tool_timeout_reason(tmp_path: Path) -> None:
    """AC6 case 4: a hanging tool call routes to escalate, reason 'tool_timeout'."""
    message_source = InMemoryMessageSource({"msg-slow": "Where is my order?"})
    model = FakeModelPort(
        [
            '{"intent": "order_status"}',
            '{"tool": "get_order_status", "args": {}}',
        ]
    )
    spy: list[str] = []
    compiled, conn = _build(tmp_path, "timeout", model, SlowToolRunner(), message_source, spy)

    config = {"configurable": {"thread_id": "case-timeout", "message_id": "msg-slow"}}
    final = compiled.invoke({"case_id": "case-timeout", "patient_id": "P-001"}, config)

    assert final.get("routing_reason") == "tool_timeout"
    assert compiled.get_state(config).next == ()
    assert len(spy) == 0
    conn.close()
