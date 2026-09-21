"""Pydantic schema for guard adversarial corpus cases."""

from typing import Literal

from pydantic import BaseModel, field_validator


class Message(BaseModel):
    """Single message in a conversation thread.

    Attributes:
        role: The speaker role, either patient or assistant.
        text: The message text.
    """

    role: Literal["patient", "assistant"]
    text: str


class GuardCase(BaseModel):
    """Schema for a guard adversarial corpus case.

    Attributes:
        case_id: Unique identifier for this case.
        family: Attack family name (one of the 7 families).
        jurisdiction: Jurisdiction code (e.g. "au").
        thread: List of messages in the thread.
        expected_verdict: Expected guard verdict ("allow" or "block").
        expected_rule_id: Expected rule id when verdict is "block".
    """

    case_id: str
    family: str
    jurisdiction: str
    thread: list[Message]
    expected_verdict: Literal["allow", "block"]
    expected_rule_id: str | None = None

    @field_validator("family")
    @classmethod
    def validate_family(cls, v: str) -> str:
        """Validate family is one of the 7 exact family strings."""
        valid_families = {
            "obfuscation",
            "homoglyph_zero_width",
            "multilingual",
            "euphemism",
            "brand_vs_generic",
            "prompt_injection",
            "quote_the_product",
        }
        if v not in valid_families:
            msg = f"Invalid family {v!r}; must be one of {valid_families}"
            raise ValueError(msg)
        return v

    @field_validator("thread")
    @classmethod
    def validate_thread_non_empty(cls, v: list[Message]) -> list[Message]:
        """Validate thread has at least one message and ends with assistant."""
        if not v:
            msg = "thread must be non-empty"
            raise ValueError(msg)
        if v[-1].role != "assistant":
            msg = "thread's last message must be from role='assistant'"
            raise ValueError(msg)
        return v

    @field_validator("expected_rule_id")
    @classmethod
    def validate_rule_id(cls, v: str | None, info):
        """Validate rule_id presence matches expected_verdict."""
        expected_verdict = info.data.get("expected_verdict")
        valid_ids = {
            "AU-G-PRODUCT",
            "AU-G-EUPHEMISM",
            "AU-G-DOSE",
            "AU-G-CONDITION",
            "AU-G-ADVICE",
        }

        if expected_verdict == "block":
            if v is None:
                msg = "block verdict requires expected_rule_id"
                raise ValueError(msg)
            if v not in valid_ids:
                msg = f"Invalid rule_id {v!r}; must be one of {valid_ids}"
                raise ValueError(msg)
        else:  # allow
            if v is not None:
                msg = "allow verdict must have expected_rule_id=None"
                raise ValueError(msg)

        return v
