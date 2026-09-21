"""HumanDecision type for approval gates."""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ValidationInfo, field_validator


class HumanDecision(BaseModel):
    """A human decision for an approval gate.

    Attributes:
        action: The decision action (approve, edit, or reject).
        decided_by: The identifier of the person making the decision.
        decided_at: The timestamp when the decision was made.
        edited_text: Optional edited text when action is "edit".
    """

    action: Literal["approve", "edit", "reject"]
    decided_by: str
    decided_at: datetime
    edited_text: Optional[str] = None

    @field_validator("edited_text")
    @classmethod
    def edited_text_required_for_edit(cls, v: Optional[str], info: ValidationInfo) -> Optional[str]:
        """Validate that edited_text is provided when action is edit."""
        action = info.data.get("action")
        if action == "edit" and not v:
            raise ValueError("edited_text is required when action is 'edit'")
        return v
