"""Load golden cases and intent elements from config files."""

from pathlib import Path
from typing import Optional

from pydantic import BaseModel, field_validator


class GoldenCase(BaseModel):
    """A single golden case for triage evaluation.

    Attributes:
        case_id: Unique case identifier.
        intent: The expected intent label.
        escalation_category: One of 'none', 'adverse_event', 'pregnancy', 'distress',
            'suspected_misuse', 'clinical_advice'.
        expected_verdict: 'allow' if escalation_category == 'none', else None.
        patient_text: The raw patient message.
        source: Origin of the case ('m1-8-corpus' or 'hand-written').
    """

    case_id: str
    intent: str
    escalation_category: str
    expected_verdict: Optional[str] = None
    patient_text: str
    source: str

    @field_validator("expected_verdict", mode="after")
    @classmethod
    def validate_expected_verdict(cls, v: Optional[str], info) -> Optional[str]:
        """Validate that expected_verdict is 'allow' iff escalation_category == 'none'."""
        escalation_category = info.data.get("escalation_category")
        if escalation_category == "none":
            if v != "allow":
                raise ValueError(
                    f"expected_verdict must be 'allow' when escalation_category is 'none', "
                    f"got {v!r}"
                )
        else:
            if v is not None:
                raise ValueError(
                    f"expected_verdict must be None when escalation_category is not 'none', "
                    f"got {v!r}"
                )
        return v


def load_golden_cases(path: Optional[Path] = None) -> list[GoldenCase]:
    """Load golden cases from cases.jsonl.

    Args:
        path: Path to cases.jsonl. If None, resolved relative to this package.

    Returns:
        List of GoldenCase objects.
    """
    import json

    if path is None:
        path = Path(__file__).resolve().parent / "cases.jsonl"

    cases = []
    with open(path) as f:
        for line in f:
            if line.strip():
                data = json.loads(line)
                cases.append(GoldenCase(**data))
    return cases


def manifest_of(cases: list[GoldenCase]) -> dict[str, str]:
    """Build a manifest dict for append-only checking.

    Args:
        cases: List of golden cases.

    Returns:
        Dict mapping case_id to composite label 'intent|escalation_category|expected_verdict'.
    """
    return {
        case.case_id: f"{case.intent}|{case.escalation_category}|{case.expected_verdict}"
        for case in cases
    }


class ConfigurationError(Exception):
    """Raised when configuration is missing or invalid."""

    pass


class IntentElements(BaseModel):
    """Intent elements configuration.

    Attributes:
        max_draft_chars: Maximum allowed draft length.
        elements: Dict mapping intent to list of required element substrings.
    """

    max_draft_chars: int
    elements: dict[str, list[str]]


def load_intent_elements(path: Optional[Path] = None) -> IntentElements:
    """Load intent elements from intent_elements.toml.

    Args:
        path: Path to intent_elements.toml. If None, resolved relative to this package.

    Returns:
        IntentElements object.

    Raises:
        ConfigurationError: If file is absent or invalid.
    """
    try:
        import tomllib
    except ImportError:
        import tomli as tomllib  # type: ignore[import-not-found]

    if path is None:
        path = Path(__file__).resolve().parent / "intent_elements.toml"

    if not path.exists():
        raise ConfigurationError(f"intent_elements.toml not found at {path}")

    try:
        with open(path, "rb") as f:
            data = tomllib.load(f)

        # Extract max_draft_chars
        max_draft_chars = data.pop("max_draft_chars", 500)

        # Build elements dict: remaining keys are intent sections with 'elements' field
        elements = {}
        for intent_name, intent_data in data.items():
            if isinstance(intent_data, dict) and "elements" in intent_data:
                elements[intent_name] = intent_data["elements"]

        return IntentElements(max_draft_chars=max_draft_chars, elements=elements)
    except ConfigurationError:
        raise
    except Exception as e:
        raise ConfigurationError(f"Failed to load intent_elements.toml: {e}") from e
