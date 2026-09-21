"""Tests for HumanDecision type."""

from datetime import datetime

import pytest
from pydantic import ValidationError

from clinicloop.hitl.decision import HumanDecision


def test_edit_decision_requires_edited_text() -> None:
    """AC3: HumanDecision with action='edit' requires edited_text field."""
    # Should fail when edited_text is missing for edit action
    with pytest.raises(ValidationError) as exc_info:
        HumanDecision(
            action="edit",
            decided_by="clinician-001",
            decided_at=datetime.now(),
            edited_text=None,
        )

    # Verify the error mentions edited_text
    assert "edited_text" in str(exc_info.value)


def test_edit_decision_with_edited_text() -> None:
    """Edit decision should succeed with edited_text."""
    decision = HumanDecision(
        action="edit",
        decided_by="clinician-001",
        decided_at=datetime.now(),
        edited_text="revised text",
    )
    assert decision.action == "edit"
    assert decision.edited_text == "revised text"


def test_approve_decision() -> None:
    """Approve decision should not require edited_text."""
    decision = HumanDecision(
        action="approve",
        decided_by="clinician-001",
        decided_at=datetime.now(),
    )
    assert decision.action == "approve"
    assert decision.edited_text is None


def test_reject_decision() -> None:
    """Reject decision should not require edited_text."""
    decision = HumanDecision(
        action="reject",
        decided_by="clinician-001",
        decided_at=datetime.now(),
    )
    assert decision.action == "reject"
    assert decision.edited_text is None
