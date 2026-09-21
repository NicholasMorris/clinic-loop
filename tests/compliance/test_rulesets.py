"""Tests for jurisdiction-keyed compliance rulesets."""

import pytest

from clinicloop.compliance.rulesets import RulesetNotImplemented, load_ruleset


def test_jurisdiction_seam_explicit_versus_unset() -> None:
    """AC1: Jurisdiction loading with explicit vs unset."""
    # Explicit UK and NZ raise RulesetNotImplemented
    with pytest.raises(RulesetNotImplemented) as exc_info:
        load_ruleset("uk")
    assert "uk" in str(exc_info.value).lower()

    with pytest.raises(RulesetNotImplemented) as exc_info:
        load_ruleset("nz")
    assert "nz" in str(exc_info.value).lower()

    # Unset (None) returns AU with fallback_active=True
    au_fallback = load_ruleset(None)
    assert au_fallback.fallback_active is True
    assert au_fallback.fallback_banner != ""

    # Explicit AU returns same rules with fallback_active=False
    au_explicit = load_ruleset("au")
    assert au_explicit.fallback_active is False
    # Rules should be identical
    assert au_explicit.rules == au_fallback.rules


def test_au_rules_have_unique_ids_and_citation_blocks() -> None:
    """AC2: AU rules have unique non-empty rule_ids and citation blocks."""
    ruleset = load_ruleset("au")

    rule_ids = []
    for rule in ruleset.rules:
        # Check rule_id exists and is non-empty
        assert hasattr(rule, "rule_id")
        assert rule.rule_id and len(rule.rule_id) > 0
        rule_ids.append(rule.rule_id)

        # Check citation block
        assert hasattr(rule, "citation")
        citation = rule.citation
        assert hasattr(citation, "instrument")
        assert hasattr(citation, "provision")
        assert hasattr(citation, "checked_date")
        assert hasattr(citation, "citation_status")
        assert citation.citation_status in ("verified", "unverified")

    # Check uniqueness
    assert len(rule_ids) == len(set(rule_ids))
