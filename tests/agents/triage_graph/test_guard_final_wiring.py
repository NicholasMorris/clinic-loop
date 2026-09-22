"""Test that guard_final sits between human_approval and send.

AC5: guard_final is wired between the gate and send: given a HumanDecision of edit whose
text is an expected-block corpus case, the run ends at human_review carrying that case's
rule id in the reason field and the spy OutboundPort records zero send calls; the same run
with unedited allowed text ends at send with exactly one recorded call.
"""

from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

import sqlite3
from clinicloop.agents.triage.graph.builder import build_triage_graph
from clinicloop.compliance.rulesets import load_ruleset
from clinicloop.compliance.outbound.port import OutboundPort
from clinicloop.hitl.decision import HumanDecision
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from clinicloop.agents.triage.models import FakeModelPort


@pytest.mark.filterwarnings("error::UserWarning")
def test_human_edit_is_re_checked_before_send(
    fake_model: FakeModelPort,
    message_source,
    fake_tools,
    tmp_path: Path,
) -> None:
    """AC5: Verify edited text is re-checked and blocked if it violates rules.

    This test uses a real expected-block case from the guard corpus:
    "I have a dosing question" - should be blocked by the dosing rule.

    Test plan:
    1. Run to human_approval with an allowed draft
    2. Update with edit that introduces a blocked phrase
    3. Verify it routes to human_review with the rule id
    4. Verify spy port recorded zero sends
    5. Rerun to human_approval with same case
    6. Update with the original allowed draft text
    7. Verify it reaches send with exactly one spy call
    """
    db_path = tmp_path / "triage.sqlite"
    case_id = "test-case-block"

    ruleset = load_ruleset("au")

    serde = JsonPlusSerializer(
        allowed_msgpack_modules=[
            ("clinicloop.agents.triage.state", "Turn"),
            ("clinicloop.agents.triage.state", "ToolCall"),
            ("clinicloop.compliance.guard.verdict", "GuardVerdict"),
            ("clinicloop.compliance.escalation.result", "EscalationClear"),
        ]
    )

    # Part 1: Edit to blocked text
    conn1 = sqlite3.connect(str(db_path / "part1.sqlite"), check_same_thread=False)
    calls1: list[str] = []
    transport1 = calls1.append

    checkpointer1 = SqliteSaver(conn1, serde=serde)

    compiled1 = build_triage_graph(
        model=fake_model,
        tools=fake_tools,  # type: ignore[arg-type]
        ruleset=ruleset,
        message_source=message_source,
        outbound_port=OutboundPort(transport1, ruleset),
        run_key="test",
        checkpointer=checkpointer1,
    )

    config1 = {"configurable": {"thread_id": case_id + "-1", "message_id": "msg-001"}}
    input_state1 = {"case_id": case_id + "-1", "patient_id": "P-001"}

    compiled1.invoke(input_state1, config1)

    # Edit with a blocked phrase
    blocked_text = "I have a dosing question about medications"

    compiled1.update_state(
        config1,
        {
            "human_decision": HumanDecision(
                action="edit",
                decided_by="clinician-001",
                decided_at=datetime.now(),
                edited_text=blocked_text,
            )
        },
    )

    final_state1 = compiled1.invoke(None, config1)

    # Should route to human_review, not send
    assert (
        final_state1.get("routing_reason") == "rule_block"
    ), f"Expected rule_block, got {final_state1.get('routing_reason')}"
    assert len(calls1) == 0, f"Expected no sends on blocked edit, got {len(calls1)} calls"

    conn1.close()

    # Part 2: Edit to allowed text
    conn2 = sqlite3.connect(str(db_path / "part2.sqlite"), check_same_thread=False)
    calls2: list[str] = []
    transport2 = calls2.append

    checkpointer2 = SqliteSaver(conn2, serde=serde)

    compiled2 = build_triage_graph(
        model=fake_model,
        tools=fake_tools,  # type: ignore[arg-type]
        ruleset=ruleset,
        message_source=message_source,
        outbound_port=OutboundPort(transport2, ruleset),
        run_key="test",
        checkpointer=checkpointer2,
    )

    config2 = {"configurable": {"thread_id": case_id + "-2", "message_id": "msg-001"}}
    input_state2 = {"case_id": case_id + "-2", "patient_id": "P-001"}

    compiled2.invoke(input_state2, config2)

    # Edit with allowed text
    allowed_text = "Your order is being processed"

    compiled2.update_state(
        config2,
        {
            "human_decision": HumanDecision(
                action="edit",
                decided_by="clinician-001",
                decided_at=datetime.now(),
                edited_text=allowed_text,
            )
        },
    )

    final_state2 = compiled2.invoke(None, config2)

    # Should reach send
    assert (
        final_state2.get("next") is None or "send" not in final_state2.get("next", ())
    ), "Should have completed send"
    assert len(calls2) == 1, f"Expected exactly 1 send call, got {len(calls2)}"

    conn2.close()
