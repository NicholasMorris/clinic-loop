"""Test that the full adversarial corpus passes the guard check.

AC1: Every expected-block case returns allowed=False with the case's
expected_rule_id in verdict.rule_ids, and every expected-allow case
returns allowed=True.
"""

import pytest

from clinicloop.compliance.guard import check
from clinicloop.compliance.rulesets import load_ruleset
from clinicloop.evals.guard.corpus_loader import load_cases
from clinicloop.evals.guard.metric import rule_violation_rate


def test_full_adversarial_corpus_passes() -> None:
    """Test that corpus passes with 0% rule violation rate.

    This test loads the merged corpus and runs check on each case,
    asserting no violations occur.
    """
    cases = load_cases()
    ruleset = load_ruleset("au")

    # Run metric function
    def check_fn(thread, jurisdiction):  # type: ignore[no-untyped-def]
        return check(thread, jurisdiction, ruleset)

    violations = rule_violation_rate(check_fn, cases)
    assert violations == 0.0, f"Corpus has {violations:.1%} violation rate"

    # Additional assertion: check verdict structure
    mismatches = []
    for case in cases:
        try:
            # Convert thread to list of dicts
            thread_dicts = [{"role": m.role, "text": m.text} for m in case.thread]
            verdict = check_fn(thread_dicts, case.jurisdiction)
        except NotImplementedError:
            mismatches.append((case.case_id, "NotImplementedError"))
            continue

        if case.expected_verdict == "block":
            if verdict.allowed:
                mismatches.append(
                    (case.case_id, f"expected block, got allowed")
                )
            elif case.expected_rule_id not in verdict.rule_ids:
                mismatches.append(
                    (
                        case.case_id,
                        f"expected {case.expected_rule_id}, got {verdict.rule_ids}",
                    )
                )
        else:  # allow
            if not verdict.allowed:
                mismatches.append(
                    (case.case_id, f"expected allow, got blocked with {verdict.rule_ids}")
                )

    if mismatches:
        msg = "Mismatching cases:\n"
        for case_id, issue in mismatches:
            msg += f"  {case_id}: {issue}\n"
        pytest.fail(msg)
