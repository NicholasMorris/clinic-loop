"""Jurisdiction-keyed compliance rulesets."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml


class RulesetNotImplemented(Exception):
    """Raised when a ruleset is not yet implemented for a jurisdiction."""

    pass


@dataclass
class Citation:
    """Citation block for a rule."""

    instrument: str
    provision: str
    checked_date: str
    citation_status: str


@dataclass
class Rule:
    """Compliance rule."""

    rule_id: str
    citation: Citation


@dataclass
class Ruleset:
    """A jurisdiction's ruleset."""

    rules: list[Rule]
    fallback_active: bool
    fallback_banner: str = ""


def load_ruleset(jurisdiction: Optional[str]) -> Ruleset:
    """Load a ruleset for the given jurisdiction.

    Args:
        jurisdiction: The jurisdiction code ('au', 'uk', 'nz') or None for default.

    Returns:
        A Ruleset for the jurisdiction.

    Raises:
        RulesetNotImplemented: If the jurisdiction is 'uk' or 'nz'.
    """
    # Normalize jurisdiction
    if jurisdiction is None:
        # Unset jurisdiction falls back to AU with banner
        jurisdiction = "au"
        fallback_active = True
        fallback_banner = (
            "Note: No explicit jurisdiction specified. "
            "Using AU ruleset as fallback. "
            "Other jurisdictions (UK, NZ) must be explicitly specified."
        )
    else:
        fallback_active = False
        fallback_banner = ""

    # Check for unimplemented jurisdictions
    if jurisdiction in ("uk", "nz"):
        raise RulesetNotImplemented(
            f"Ruleset for jurisdiction '{jurisdiction}' is not yet implemented"
        )

    # Load the ruleset from YAML
    rules_dir = Path(__file__).parent / "rules"
    ruleset_file = rules_dir / f"{jurisdiction}.yaml"

    if not ruleset_file.exists():
        raise ValueError(f"Ruleset file not found: {ruleset_file}")

    with open(ruleset_file) as f:
        data = yaml.safe_load(f) or {}

    # Parse rules
    rules_data = data.get("rules", [])
    rules = []
    for rule_data in rules_data:
        citation_data = rule_data.get("citation", {})
        citation = Citation(
            instrument=citation_data.get("instrument", ""),
            provision=citation_data.get("provision", ""),
            checked_date=citation_data.get("checked_date", ""),
            citation_status=citation_data.get("citation_status", "unverified"),
        )
        rule = Rule(
            rule_id=rule_data.get("rule_id", ""),
            citation=citation,
        )
        rules.append(rule)

    return Ruleset(
        rules=rules,
        fallback_active=fallback_active,
        fallback_banner=fallback_banner,
    )
