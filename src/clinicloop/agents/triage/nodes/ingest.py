"""Ingest node: redact PII and detect language."""

from typing import Any

from clinicloop.agents.triage.language import detect_language
from clinicloop.agents.triage.prompts import build_data_block
from clinicloop.agents.triage.state import Turn
from clinicloop.compliance.redaction import redact_with_pseudonyms


def ingest(state: dict[str, Any], raw_message: str, run_key: str) -> dict[str, Any]:
    """Redact PII from raw patient message and detect language.

    Args:
        state: Current TriageState as dict (for type flexibility during graph execution).
        raw_message: Raw unredacted patient message.
        run_key: Key for consistent pseudonym hashing within this run.

    Returns:
        State update dict with redacted_thread, patient_data_block, and language.
    """
    # Redact the message
    redacted_text = redact_with_pseudonyms(raw_message, run_key)

    # Detect language from redacted text
    language = detect_language(redacted_text)

    # Create redacted thread
    redacted_thread = [Turn(role="patient", text=redacted_text)]

    # Create delimited patient data block
    patient_data_block = build_data_block(redacted_text)

    return {
        "redacted_thread": redacted_thread,
        "patient_data_block": patient_data_block,
        "language": language,
    }
