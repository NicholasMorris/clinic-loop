"""Test corpus shape: all families present, floor met, unique case ids."""

from typing import Any

from clinicloop.evals.guard import FAMILIES, MIN_PER_FAMILY, load_cases


def test_seven_families_present_with_floor_and_unique_case_ids() -> None:
    """AC1: Every family present with >=12 cases and all ids unique."""
    cases = load_cases()

    # Group by family
    by_family: dict[str, list[Any]] = {}
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

    # Check that corpus files are ASCII-only with \uXXXX escapes
    from pathlib import Path

    corpus_dir = Path(__file__).resolve().parents[4] / "evals" / "guard" / "corpus"
    for jsonl_file in corpus_dir.glob("*.jsonl"):
        with open(jsonl_file, "rb") as f:
            raw = f.read()
            try:
                raw.decode("ascii")
            except UnicodeDecodeError:
                assert False, f"Non-ASCII bytes in {jsonl_file.name}"


def test_each_family_has_block_and_allow_floor_and_rule_ids_are_spread() -> None:
    """Per family: >=12 block and >=4 allow; each rule id has >=6 block cases; threads differ."""
    from collections import Counter

    cases = load_cases()
    verdicts = Counter((c.family, c.expected_verdict) for c in cases)
    for family in FAMILIES:
        assert verdicts[(family, "block")] >= 12, f"{family} block: {verdicts[(family, 'block')]}"
        assert verdicts[(family, "allow")] >= 4, f"{family} allow: {verdicts[(family, 'allow')]}"

    rule_counts = Counter(c.expected_rule_id for c in cases if c.expected_verdict == "block")
    for rule_id in (
        "AU-G-PRODUCT",
        "AU-G-EUPHEMISM",
        "AU-G-DOSE",
        "AU-G-CONDITION",
        "AU-G-ADVICE",
    ):
        assert rule_counts[rule_id] >= 6, f"{rule_id}: {rule_counts[rule_id]} block cases"

    threads = [tuple((m.role, m.text) for m in c.thread) for c in cases]
    assert len(set(threads)) == len(threads), "duplicate threads in corpus"


def test_corpus_text_avoids_forbidden_words() -> None:
    """Fixture text must not contain the lint's forbidden words."""
    for case in load_cases():
        text = " ".join(m.text for m in case.thread).lower()
        for word in ("fraud", "abuse", "drug seeker"):
            assert word not in text, f"{case.case_id} contains {word!r}"
