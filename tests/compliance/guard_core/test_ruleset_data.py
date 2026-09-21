"""Test AU ruleset data structure and validation.

AC7: Every rule in au.yaml carries instrument, provision, checked_date
and citation_status; escalation_routing gives each of adverse_event,
suspected_misuse, distress, pregnancy and clinical_advice with queue
name, value_source "assumed" and integer target_response_minutes;
loader raises RulesetValidationError when keys are absent; naming lint
reports zero matches over au.yaml.
"""

import tempfile
from pathlib import Path

import pytest

from clinicloop.compliance.rulesets import (
    RulesetValidationError,
    load_ruleset,
    load_ruleset_file,
)
from clinicloop.naminglint.lint import load_i6_words


def test_au_rules_carry_citations_and_escalation_routing() -> None:
    """Test AU ruleset has proper citation and escalation data."""
    ruleset = load_ruleset("au")

    # Check each rule has citation fields
    for rule in ruleset.rules:
        assert rule.citation.instrument, f"Rule {rule.rule_id} missing instrument"
        assert rule.citation.provision, f"Rule {rule.rule_id} missing provision"
        assert rule.citation.checked_date, f"Rule {rule.rule_id} missing checked_date"
        assert rule.citation.citation_status in (
            "verified",
            "unverified",
        ), f"Rule {rule.rule_id} has invalid citation_status"

    # Check escalation routing
    assert ruleset.escalation_routing, "ruleset missing escalation_routing"

    required_categories = {
        "adverse_event",
        "suspected_misuse",
        "distress",
        "pregnancy",
        "clinical_advice",
    }
    routing_categories = {er.category for er in ruleset.escalation_routing}

    missing = required_categories - routing_categories
    assert not missing, f"escalation_routing missing categories: {missing}"

    # Check escalation route values
    for route in ruleset.escalation_routing:
        assert route.queue, f"Route {route.category} missing queue"
        assert route.value_source == "assumed", (
            f"Route {route.category} value_source should be 'assumed'"
        )
        assert isinstance(route.target_response_minutes, int), (
            f"Route {route.category} target_response_minutes must be int"
        )
        assert route.target_response_minutes > 0

    # Check specific values from spec
    expected_minutes = {
        "adverse_event": 15,
        "distress": 15,
        "suspected_misuse": 60,
        "pregnancy": 60,
        "clinical_advice": 240,
    }

    for category, expected_minutes_val in expected_minutes.items():
        route_opt = next((r for r in ruleset.escalation_routing if r.category == category), None)
        assert route_opt is not None, f"Missing route for {category}"
        route = route_opt
        actual_minutes = route.target_response_minutes
        assert actual_minutes == expected_minutes_val, (
            f"Route {category} has {actual_minutes} minutes, expected {expected_minutes_val}"
        )


def test_ruleset_validation_errors() -> None:
    """Test that loader raises RulesetValidationError for invalid YAML."""
    # Create temp YAML with missing escalation_routing
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Missing escalation_routing
        yaml_missing_routing = tmppath / "missing_routing.yaml"
        yaml_missing_routing.write_text("""
jurisdiction: au
version: "2026-09-22.1"
lexicon:
  products: []
rules: []
""")
        with pytest.raises(RulesetValidationError):
            load_ruleset_file(yaml_missing_routing)

        # Missing category in escalation_routing
        yaml_missing_category = tmppath / "missing_category.yaml"
        yaml_missing_category.write_text("""
jurisdiction: au
version: "2026-09-22.1"
lexicon:
  products: []
escalation_routing:
  - category: adverse_event
    queue: clinical_urgent
    target_response_minutes: 15
    value_source: assumed
rules: []
""")
        with pytest.raises(RulesetValidationError):
            load_ruleset_file(yaml_missing_category)

        # Non-integer target_response_minutes
        yaml_bad_type = tmppath / "bad_type.yaml"
        yaml_bad_type.write_text("""
jurisdiction: au
version: "2026-09-22.1"
lexicon:
  products: []
escalation_routing:
  - category: adverse_event
    queue: clinical_urgent
    target_response_minutes: "15"
    value_source: assumed
rules: []
""")
        with pytest.raises(RulesetValidationError):
            load_ruleset_file(yaml_bad_type)


def test_au_yaml_naming_lint_clean() -> None:
    """Test that au.yaml has zero naming lint matches."""
    from clinicloop.naminglint.lint import get_repo_root

    repo_root = get_repo_root()
    i6_words = load_i6_words(repo_root)

    # Scan just the au.yaml file
    au_yaml = repo_root / "src" / "clinicloop" / "compliance" / "rules" / "au.yaml"
    au_content = au_yaml.read_text()

    # Check for I6 words
    i6_matches = []
    for i6_word in i6_words:
        if i6_word and i6_word.lower() in au_content.lower():
            i6_matches.append(i6_word)

    assert not i6_matches, f"au.yaml contains forbidden I6 words: {i6_matches}"
