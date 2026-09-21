"""Test corpus schema: every case validates against GuardCase."""

from pydantic import ValidationError

from clinicloop.evals.guard import GuardCase, load_cases


def test_every_case_validates_against_guard_case_model() -> None:
    """AC2: Every case in corpus validates; hand-made cases with wrong schema fail."""
    cases = load_cases()

    # All loaded cases should be valid GuardCase (already validated via model_validate)
    assert len(cases) > 0, "No cases loaded"

    # Test negative: block case without expected_rule_id should fail
    bad_block = {
        "case_id": "bad-001",
        "family": "obfuscation",
        "jurisdiction": "au",
        "thread": [
            {"role": "patient", "text": "Test"},
            {"role": "assistant", "text": "Test response"},
        ],
        "expected_verdict": "block",
        "expected_rule_id": None,  # Invalid: block needs a rule id
    }

    with_error_block = False
    try:
        GuardCase.model_validate(bad_block)
    except ValidationError:
        with_error_block = True

    assert with_error_block, "block verdict without expected_rule_id should fail validation"

    # Test negative: allow case with expected_rule_id should fail
    bad_allow = {
        "case_id": "bad-002",
        "family": "euphemism",
        "jurisdiction": "au",
        "thread": [
            {"role": "patient", "text": "Test"},
            {"role": "assistant", "text": "Safe response"},
        ],
        "expected_verdict": "allow",
        "expected_rule_id": "AU-G-PRODUCT",  # Invalid: allow should not have rule id
    }

    with_error_allow = False
    try:
        GuardCase.model_validate(bad_allow)
    except ValidationError:
        with_error_allow = True

    assert with_error_allow, "allow verdict with expected_rule_id should fail validation"

    # All loaded cases should pass
    invalid = []
    for case in cases:
        try:
            GuardCase.model_validate(case.model_dump())
        except ValidationError as e:
            invalid.append((case.case_id, str(e)))

    assert invalid == [], f"Invalid cases: {invalid}"
