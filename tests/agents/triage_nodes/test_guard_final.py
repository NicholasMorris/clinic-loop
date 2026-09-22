"""Test guard_final node.

AC6: guard_final re-checks post-edit text: given an approved state whose
human-edited text is an expected-block corpus case, guard_final returns a verdict
with allowed False carrying that case's rule id and sets routing reason "rule_block"
with the same id, while the pre-edit text alone returns allowed True.
"""

from datetime import datetime

import pytest

from clinicloop.agents.triage.nodes.guard_final import guard_final
from clinicloop.agents.triage.state import Turn
from clinicloop.compliance.rulesets import Ruleset, load_ruleset
from clinicloop.evals.guard import GuardCase, load_cases
from clinicloop.hitl.decision import HumanDecision


@pytest.fixture
def _fixed_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set CLINICLOOP_ESCALATION_KEY to a fixed value."""
    monkeypatch.setenv("CLINICLOOP_ESCALATION_KEY", "a" * 64)


@pytest.fixture
def ruleset() -> Ruleset:
    """Load AU ruleset for checks."""
    return load_ruleset("au")


def _real_block_case() -> GuardCase:
    """A real expected-block corpus case (not a hand-typed real drug name)."""
    return next(c for c in load_cases() if c.expected_verdict == "block")


def test_human_edit_is_re_checked_after_approval(ruleset: Ruleset, _fixed_key: None) -> None:
    """AC6: an edit to a real expected-block corpus case is blocked with its rule id."""
    block_case = _real_block_case()
    edited_text = next(m.text for m in block_case.thread if m.role == "assistant")

    thread = [Turn(role="patient", text="Can you help with my prescriptions?")]
    pre_edit_draft = "Sure, I'm happy to help with your order."

    state_dict = {
        "case_id": "c-001",
        "patient_id": "p-001",
        "redacted_thread": thread,
        "draft": pre_edit_draft,
        "guard_verdicts": [],
        "human_decision": HumanDecision(
            action="edit",
            decided_by="clinician-001",
            decided_at=datetime.now(),
            edited_text=edited_text,
        ),
    }

    update = guard_final(state_dict, ruleset)

    verdicts = update["guard_verdicts"]
    assert len(verdicts) == 1
    latest_verdict = verdicts[-1]
    assert latest_verdict.allowed is False
    assert block_case.expected_rule_id in latest_verdict.rule_ids
    assert update.get("routing_reason") == "rule_block"
    assert block_case.expected_rule_id in update.get("routing_rule_ids", ())

    # The pre-edit draft alone (no edit applied) is allowed.
    approved_state = {**state_dict, "guard_verdicts": []}
    approved_state["human_decision"] = HumanDecision(
        action="approve", decided_by="clinician-001", decided_at=datetime.now()
    )
    approved_update = guard_final(approved_state, ruleset)
    assert approved_update["guard_verdicts"][-1].allowed is True
    assert approved_update.get("routing_reason") is None


def test_guard_final_requires_human_decision(ruleset: Ruleset, _fixed_key: None) -> None:
    """AC6: guard_final raises ValueError if human_decision is None."""
    state_dict = {
        "case_id": "c-002",
        "patient_id": "p-002",
        "redacted_thread": [
            Turn(role="patient", text="I have a question about my order"),
            Turn(role="assistant", text="I can help."),
        ],
        "draft": "Your order is on the way.",
        "human_decision": None,  # No decision
    }

    with pytest.raises(ValueError):
        guard_final(state_dict, ruleset)


def test_guard_final_checks_approved_text(ruleset: Ruleset, _fixed_key: None) -> None:
    """AC6: an approved, benign draft is checked and allowed."""
    thread = [
        Turn(role="patient", text="Do you offer international shipping?"),
        Turn(role="assistant", text="I can help with that."),
    ]

    draft_text = "Yes, we ship internationally to most regions."

    state_dict = {
        "case_id": "c-003",
        "patient_id": "p-003",
        "redacted_thread": thread,
        "draft": draft_text,
        "guard_verdicts": [],
        "human_decision": HumanDecision(
            action="approve",
            decided_by="clinician-001",
            decided_at=datetime.now(),
        ),
    }

    update = guard_final(state_dict, ruleset)

    assert "guard_verdicts" in update
    verdicts = update["guard_verdicts"]
    assert len(verdicts) == 1
    assert verdicts[-1].allowed is True
    assert update.get("routing_reason") is None


def test_pre_edit_vs_post_edit_verdicts(ruleset: Ruleset, _fixed_key: None) -> None:
    """AC6: guard_final checks the post-edit text, not the pre-edit draft."""
    block_case = _real_block_case()
    post_edit = next(m.text for m in block_case.thread if m.role == "assistant")

    thread = [Turn(role="patient", text="Can you help with my prescriptions?")]
    pre_edit = "Sure, happy to help with your order."

    state_dict = {
        "case_id": "c-004",
        "patient_id": "p-004",
        "redacted_thread": thread,
        "draft": pre_edit,
        "guard_verdicts": [],
        "human_decision": HumanDecision(
            action="edit",
            decided_by="clinician-001",
            decided_at=datetime.now(),
            edited_text=post_edit,
        ),
    }

    update = guard_final(state_dict, ruleset)

    verdicts = update["guard_verdicts"]
    assert len(verdicts) == 1
    # The verdict is based on the edited text (blocked), not the pre-edit draft (which
    # names no product and would have been allowed).
    assert verdicts[-1].allowed is False
    assert block_case.expected_rule_id in verdicts[-1].rule_ids
