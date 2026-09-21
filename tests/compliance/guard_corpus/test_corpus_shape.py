"""Test corpus shape: all families present, floor met, unique case ids."""

from clinicloop.evals.guard import FAMILIES, MIN_PER_FAMILY, load_cases


def test_seven_families_present_with_floor_and_unique_case_ids() -> None:
    """AC1: Every family present with >=12 cases and all ids unique."""
    cases = load_cases()

    # Group by family
    by_family = {}
    for case in cases:
        if case.family not in by_family:
            by_family[case.family] = []
        by_family[case.family].append(case)

    # Check all families present
    missing_families = set(FAMILIES) - set(by_family.keys())
    assert missing_families == set(), f"Missing families: {missing_families}"

    # Check floor per family
    for family in FAMILIES:
        count = len(by_family.get(family, []))
        assert count >= MIN_PER_FAMILY, f"{family}: {count} < {MIN_PER_FAMILY}"

    # Check uniqueness
    case_ids = [c.case_id for c in cases]
    duplicates = [cid for cid in case_ids if case_ids.count(cid) > 1]
    assert duplicates == [], f"Duplicate case ids: {set(duplicates)}"

    # Check ASCII only with \uXXXX escapes (thread text should not have raw non-ASCII)
    for case in cases:
        for msg in case.thread:
            try:
                msg.text.encode("ascii")
            except UnicodeEncodeError:
                msg_preview = msg.text[:50]
                msg_preview_escaped = repr(msg.text[:50])
                assert False, f"Non-ASCII in case {case.case_id}: {msg_preview_escaped}"
