"""Jurisdiction-keyed compliance rulesets."""

from dataclasses import dataclass
from typing import Optional


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
    raise NotImplementedError()
