"""Test the golden set for append-only property and label coverage."""

from clinicloop.agents.triage.intents import Intent
from clinicloop.evals.guard.baseline import append_only_diff
from evals.triage.golden.loader import load_golden_cases, manifest_of


def test_append_only_labels_in_enum_and_per_label_floor():
    """AC1: Golden set is append-only; labels are in enums; per-label floor is 5."""
    cases = load_golden_cases()

    # Build manifest
    current_manifest = manifest_of(cases)

    # Simulate a prior with one removed id and one label changed
    synthetic_prior = {
        case_id: label for case_id, label in current_manifest.items()
    }
    synthetic_prior["tg-0007"] = "order_status|none|allow"  # Add a removed case
    # Change one label to test reversal detection
    if cases:
        first_case_id = cases[0].case_id
        parts = synthetic_prior[first_case_id].split("|")
        parts[0] = "unknown"  # Change intent to unknown
        synthetic_prior[first_case_id] = "|".join(parts)

    # Check append-only: should raise AppendOnlyViolation for removed and reversed
    try:
        append_only_diff(synthetic_prior, current_manifest)
        assert False, "Should have raised AppendOnlyViolation"
    except Exception as e:
        # Expect "Append-only violation" in the message
        assert "removed" in str(e) or "reversed" in str(e)

    # Now check against no prior (first baseline)
    result = append_only_diff(None, current_manifest)
    assert result.first_baseline is True
    assert result.removed == []
    assert result.reversed == []

    # Verify all intents are valid
    valid_intents = {intent.value for intent in Intent}
    for case in cases:
        assert case.intent in valid_intents, f"Invalid intent: {case.intent}"

    # Verify all escalation categories are valid
    valid_escalations = {"none", "adverse_event", "pregnancy", "distress", "suspected_misuse", "clinical_advice"}
    for case in cases:
        assert case.escalation_category in valid_escalations, (
            f"Invalid escalation: {case.escalation_category}"
        )

    # Check per-intent floor
    intent_counts = {}
    for case in cases:
        intent_counts[case.intent] = intent_counts.get(case.intent, 0) + 1

    print(f"Intent counts: {intent_counts}")
    for intent, count in intent_counts.items():
        assert count >= 5, f"Intent {intent} has only {count} cases, need >= 5"

    # Check per-escalation-category floor
    escalation_counts = {}
    for case in cases:
        escalation_counts[case.escalation_category] = escalation_counts.get(case.escalation_category, 0) + 1

    print(f"Escalation counts: {escalation_counts}")
    for escalation, count in escalation_counts.items():
        assert count >= 5, f"Escalation {escalation} has only {count} cases, need >= 5"
