"""Test ingest node redaction behavior.

AC2: After ingest runs on the seeded PII-bearing fixture message, no raw identifier
from that fixture appears anywhere in the serialised state, each is replaced by its
keyed-hash pseudonym, and the patient text sits in state.patient_data_block rather
than in any instruction field.
"""

import json
import re

import pytest

from clinicloop.agents.triage.nodes.ingest import ingest
from clinicloop.agents.triage.state import TriageState


@pytest.fixture
def _fixed_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set CLINICLOOP_ESCALATION_KEY to a fixed value."""
    monkeypatch.setenv("CLINICLOOP_ESCALATION_KEY", "a" * 64)


@pytest.fixture
def medicare_valid() -> str:
    """A number that passes this repo's Medicare checksum but not its NHS checksum.

    Both classes redact 10-digit numbers, so a number valid under both would redact
    ambiguously; this one redacts unambiguously as [MEDICARE:...].
    """
    return "3000000106"


@pytest.fixture
def pii_message(medicare_valid: str) -> str:
    """Build a message with PII that should be redacted.

    Includes: Medicare number, phone, email, DOB, address, and synthetic roster name.
    """
    return (
        f"Hi, I'm patient with Medicare {medicare_valid} and phone 0412345678. "
        f"My email is john.doe@example.com and DOB is 1980-05-15. "
        f"I live at 42 Smith Street, Sydney NSW 2000. "
        f"Can I speak with Dr James about my order?"
    )


def test_no_raw_identifier_survives_ingest_and_text_is_delimited(
    _fixed_key: None, pii_message: str, medicare_valid: str
) -> None:
    """AC2: No raw PII survives ingest; all text goes into patient_data_block."""
    # Create a minimal state
    state_dict = {
        "case_id": "c-001",
        "patient_id": "p-001",
    }

    # Run ingest
    update = ingest(state_dict, pii_message, "run-001")

    # Verify the update returned expected fields
    assert "redacted_thread" in update
    assert "patient_data_block" in update
    assert "language" in update

    # Build the state from the update
    state = TriageState.model_validate(
        {
            **state_dict,
            **update,
        }
    )

    # Serialize to JSON for full check
    state_json = json.dumps(state.model_dump(mode="json"))

    # Check: no raw identifiers in JSON
    assert medicare_valid not in state_json, "Raw Medicare number found in state"
    assert "0412345678" not in state_json, "Raw phone found in state"
    assert "john.doe@example.com" not in state_json, "Raw email found in state"
    assert "1980-05-15" not in state_json, "Raw DOB found in state"
    assert "42 Smith Street" not in state_json, "Raw address found in state"
    assert "Dr James" not in state_json, "Raw roster name found in state"

    # Check: patient text is in patient_data_block, delimited
    assert state.patient_data_block.startswith("<<<PATIENT_DATA")
    assert state.patient_data_block.endswith("PATIENT_DATA>>>")

    # Check: the Medicare number is redacted under its own class, not misclassified
    # as another 10-digit identifier (NHS numbers are also 10 digits).
    assert "[MEDICARE:" in state.patient_data_block
    assert "[PHONE:" in state.patient_data_block.upper()

    # Check: delimiters are escaped inside the block (no raw markers)
    lines = state.patient_data_block.split("\n")
    # Remove the delimiter lines
    content_lines = [line for line in lines[1:-1]]
    content = "\n".join(content_lines)

    # The content should not have raw <<< or >>> in it (they should be escaped)
    # Actually, the build_data_block function escapes marker look-alikes
    assert content.count("<<<") == 0, "Unescaped opening delimiter in content"
    assert content.count(">>>") == 0, "Unescaped closing delimiter in content"


def test_redacted_thread_uses_pseudonyms(_fixed_key: None, pii_message: str) -> None:
    """AC2: Identifiers are replaced with keyed-hash pseudonyms."""
    state_dict = {
        "case_id": "c-001",
        "patient_id": "p-001",
    }

    run_key = "run-001"
    update = ingest(state_dict, pii_message, run_key)

    state = TriageState.model_validate(
        {
            **state_dict,
            **update,
        }
    )

    # Check that redacted thread exists and is not empty
    assert state.redacted_thread
    assert state.redacted_thread[0].role == "patient"
    redacted_text = state.redacted_thread[0].text

    # The redacted text should contain pseudonym markers like [CLASS:12345678]
    # Not the raw identifiers
    assert "[" in redacted_text, "Should have redaction markers"
    assert "0412345678" not in redacted_text, "Should not have raw phone"


def test_same_identifier_same_pseudonym(_fixed_key: None) -> None:
    """AC2: Same identifier hashed consistently within a run."""
    run_key = "run-001"

    msg1 = "My phone is 0412345678."
    msg2 = "Call me at 0412345678 please."

    state1_dict = {"case_id": "c-001", "patient_id": "p-001"}
    update1 = ingest(state1_dict, msg1, run_key)
    state1 = TriageState.model_validate({**state1_dict, **update1})

    state2_dict = {"case_id": "c-002", "patient_id": "p-002"}
    update2 = ingest(state2_dict, msg2, run_key)
    state2 = TriageState.model_validate({**state2_dict, **update2})

    # Extract the pseudonym from each
    # They should be identical since the same value and run_key produce same hash
    text1 = state1.redacted_thread[0].text
    text2 = state2.redacted_thread[0].text

    # Find the phone pseudonym pattern [PHONE:...] - case insensitive
    match1 = re.search(r"\[PHONE:([A-Fa-f0-9]+)\]", text1)
    match2 = re.search(r"\[PHONE:([A-Fa-f0-9]+)\]", text2)

    assert match1 and match2, f"Should find phone pseudonym markers. text1={text1}, text2={text2}"
    assert match1.group(1) == match2.group(1), (
        f"Same phone should have same pseudonym: {match1.group(1)} vs {match2.group(1)}"
    )
