"""Test escalation result routing from ruleset."""

import dataclasses

import pytest

from clinicloop.compliance.escalation.detector import detect
from clinicloop.compliance.rulesets import RulesetValidationError, load_ruleset


@pytest.fixture
def ruleset():
    """Load AU ruleset."""
    return load_ruleset("au")


def test_result_carries_queue_and_target_response_time_from_ruleset(ruleset):
    """AC6: Result carries queue and target_response_minutes from ruleset.

    For the AU ruleset:
    - adverse_event: 15 minutes, clinical_urgent queue
    - distress: 15 minutes, clinical_urgent queue
    - suspected_misuse: 60 minutes, integrity_review queue
    - pregnancy: 60 minutes, prescriber_review queue
    - clinical_advice: 240 minutes, prescriber_review queue

    When category is 'none', both fields are None.
    A ruleset missing escalation_routing raises RulesetValidationError.
    """
    # Test adverse_event routing
    thread_adverse = [{"role": "patient", "text": "I took too many tablets and have chest pain."}]
    result = detect(thread_adverse, ruleset)
    assert result.category == "adverse_event"
    assert result.queue == "clinical_urgent"
    assert result.target_response_minutes == 15

    # Test distress routing
    thread_distress = [{"role": "patient", "text": "I want to die. Life is hopeless."}]
    result = detect(thread_distress, ruleset)
    assert result.category == "distress"
    assert result.queue == "clinical_urgent"
    assert result.target_response_minutes == 15

    # Test suspected_misuse routing
    thread_misuse = [
        {
            "role": "patient",
            "text": "I took extra tablets because I ran out early.",
        }
    ]
    result = detect(thread_misuse, ruleset)
    assert result.category == "suspected_misuse"
    assert result.queue == "integrity_review"
    assert result.target_response_minutes == 60

    # Test pregnancy routing
    thread_pregnancy = [
        {
            "role": "patient",
            "text": "I missed my period and might be pregnant.",
        }
    ]
    result = detect(thread_pregnancy, ruleset)
    assert result.category == "pregnancy"
    assert result.queue == "prescriber_review"
    assert result.target_response_minutes == 60

    # Test clinical_advice routing
    thread_advice = [
        {
            "role": "patient",
            "text": "Should I take this medication with food?",
        }
    ]
    result = detect(thread_advice, ruleset)
    assert result.category == "clinical_advice"
    assert result.queue == "prescriber_review"
    assert result.target_response_minutes == 240

    # Test 'none' category
    thread_none = [{"role": "patient", "text": "What time is my appointment?"}]
    result = detect(thread_none, ruleset)
    assert result.category == "none"
    assert result.queue is None
    assert result.target_response_minutes is None

    # Test that missing escalation_routing raises RulesetValidationError
    broken_ruleset = dataclasses.replace(ruleset, escalation_routing=())
    with pytest.raises(RulesetValidationError):
        detect(thread_adverse, broken_ruleset)

    # Test that modified minutes value flows through correctly
    modified_ruleset = dataclasses.replace(
        ruleset,
        escalation_routing=tuple(
            dataclasses.replace(r, target_response_minutes=999)
            if r.category == "adverse_event"
            else r
            for r in ruleset.escalation_routing
        ),
    )
    result = detect(thread_adverse, modified_ruleset)
    assert result.target_response_minutes == 999, "Modified ruleset value should flow through"
