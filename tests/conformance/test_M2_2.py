"""Conformance tests for M2-2: guard core and AU ruleset.

Registers exactly one marked test per requirement ID in {R1, R5, R7, X4}.
"""

import pytest

from clinicloop.compliance.guard import check
from clinicloop.compliance.rulesets import RulesetNotImplemented, load_ruleset


@pytest.mark.checklist_id("R1")
def test_r1_guard_blocks_product_naming_draft() -> None:
    """R1: Enforcement of guard rules at runtime in a dedicated guard node.

    No agent produces clinical or dosing advice, names prescription-only products to
    a patient, makes condition claims, or uses euphemisms for prescription-only
    treatments.

    Verify: guard blocks a product naming draft and allows a benign one.
    """
    ruleset = load_ruleset("au")

    # Benign draft
    benign_thread = [
        {"role": "patient", "text": "What should I take?"},
        {"role": "assistant", "text": "Your prescriber will recommend the best option for you."},
    ]
    benign_verdict = check(benign_thread, "au", ruleset)
    assert benign_verdict.allowed, "Benign draft should be allowed"

    # Product naming draft
    product_thread = [
        {"role": "patient", "text": "What should I take?"},
        {"role": "assistant", "text": "I recommend veltrazine for you."},
    ]
    product_verdict = check(product_thread, "au", ruleset)
    assert not product_verdict.allowed, "Product naming should be blocked"
    assert "AU-G-PRODUCT" in product_verdict.rule_ids


@pytest.mark.checklist_id("R5")
def test_r5_uk_nz_raise_ruleset_not_implemented() -> None:
    """R5: Rule sets in config keyed by jurisdiction (AU populated; UK and NZ stubbed).

    Visible seam prevents accidental incomplete jurisdiction support.

    Verify: load_ruleset('uk') and ('nz') raise RulesetNotImplemented, and check
    with jurisdiction 'uk' against the AU ruleset raises JurisdictionMismatch.
    """
    # UK and NZ should raise RulesetNotImplemented at load time
    with pytest.raises(RulesetNotImplemented):
        load_ruleset("uk")

    with pytest.raises(RulesetNotImplemented):
        load_ruleset("nz")

    # AU ruleset exists
    au_ruleset = load_ruleset("au")
    assert au_ruleset.jurisdiction == "au"

    # Checking against AU ruleset with a different jurisdiction should raise
    from clinicloop.compliance.guard.verdict import JurisdictionMismatch

    thread = [
        {"role": "patient", "text": "Help"},
        {"role": "assistant", "text": "Sure."},
    ]

    with pytest.raises(JurisdictionMismatch):
        check(thread, "uk", au_ruleset)


@pytest.mark.checklist_id("R7")
def test_r7_au_yaml_contains_no_forbidden_words() -> None:
    """R7: Cite statute/code sections neutrally, no enforcement history.

    Do not reference any company's regulatory or enforcement history; do not name
    any specific clinic anywhere in the repo. Naming lint enforces this.

    Verify: au.yaml text contains none of the naming lint's forbidden words.
    """
    from pathlib import Path

    from clinicloop.naminglint.lint import load_i6_words

    repo_root = Path(__file__).resolve().parents[2]
    au_yaml_path = repo_root / "src" / "clinicloop" / "compliance" / "rules" / "au.yaml"

    au_content = au_yaml_path.read_text()

    forbidden_words = load_i6_words(repo_root)
    assert forbidden_words, "the lint's forbidden word list must not be empty"

    for word in forbidden_words:
        assert word.lower() not in au_content.lower(), "au.yaml contains a forbidden word"


@pytest.mark.checklist_id("X4")
def test_x4_docs_and_tests_exist() -> None:
    """X4: Depth over breadth; cut features before tests, evals, docs.

    Verify: docs/compliance/guard.md and tests/compliance/guard_core/test_corpus_green.py
    exist.
    """
    from pathlib import Path

    repo_root = Path(__file__).resolve().parents[2]

    guard_docs = repo_root / "docs" / "compliance" / "guard.md"
    assert guard_docs.exists(), f"Missing {guard_docs}"

    corpus_test = repo_root / "tests" / "compliance" / "guard_core" / "test_corpus_green.py"
    assert corpus_test.exists(), f"Missing {corpus_test}"
