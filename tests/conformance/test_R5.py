"""Conformance test R5: Rule sets in config keyed by jurisdiction.

Tests that rulesets are jurisdiction-keyed, AU populated, UK and NZ stubbed.
"""

import pytest

from clinicloop.compliance.rulesets import RulesetNotImplemented, load_ruleset


@pytest.mark.checklist_id("R5")
def test_jurisdiction_keyed_rulesets() -> None:
    """R5: Rulesets are jurisdiction-keyed (AU populated; UK and NZ stubbed)."""
    # AU should work
    au_rules = load_ruleset("au")
    assert au_rules is not None
    assert len(au_rules.rules) > 0

    # UK and NZ should raise RulesetNotImplemented
    with pytest.raises(RulesetNotImplemented):
        load_ruleset("uk")

    with pytest.raises(RulesetNotImplemented):
        load_ruleset("nz")

    # Unset should default to AU
    default_rules = load_ruleset(None)
    assert default_rules.fallback_active is True
    assert len(default_rules.rules) > 0
