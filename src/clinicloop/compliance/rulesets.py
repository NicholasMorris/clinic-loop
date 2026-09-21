"""Jurisdiction-keyed compliance rulesets."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml


class RulesetNotImplemented(Exception):
    """Raised when a ruleset is not yet implemented for a jurisdiction."""

    pass


class RulesetValidationError(ValueError):
    """Raised when a ruleset is invalid."""

    pass


@dataclass(frozen=True)
class Citation:
    """Citation block for a rule."""

    instrument: str
    provision: str
    checked_date: str
    citation_status: str


@dataclass(frozen=True)
class Rule:
    """Compliance rule."""

    rule_id: str
    citation: Citation


@dataclass(frozen=True)
class EscalationRoute:
    """Escalation routing for a rule category."""

    category: str
    queue: str
    target_response_minutes: int
    value_source: str


@dataclass(frozen=True)
class Lexicon:
    """Lexicon of products, euphemisms, and conditions."""

    products: tuple[str, ...]
    euphemisms: tuple[str, ...]
    conditions: tuple[str, ...]


@dataclass(frozen=True)
class Ruleset:
    """A jurisdiction's ruleset."""

    jurisdiction: str
    version: str
    rules: tuple[Rule, ...]
    lexicon: Lexicon
    escalation_routing: tuple[EscalationRoute, ...]
    second_opinion_enabled: bool = False
    fallback_active: bool = False
    fallback_banner: str = ""


def load_ruleset_file(filepath: Path) -> Ruleset:
    """Load a ruleset from a YAML file.

    Args:
        filepath: Path to the YAML file.

    Returns:
        A Ruleset.

    Raises:
        RulesetValidationError: If required fields are missing or invalid.
    """
    with open(filepath) as f:
        data = yaml.safe_load(f) or {}

    # Extract top-level fields
    jurisdiction = data.get("jurisdiction")
    version = data.get("version")
    lexicon_data = data.get("lexicon", {})
    escalation_routing_data = data.get("escalation_routing", [])
    second_opinion_data = data.get("second_opinion", {})
    rules_data = data.get("rules", [])

    # Validate required fields
    if not version:
        raise RulesetValidationError("Missing 'version' in ruleset")

    if not lexicon_data:
        raise RulesetValidationError("Missing 'lexicon' in ruleset")

    if not escalation_routing_data:
        raise RulesetValidationError("Missing 'escalation_routing' in ruleset")

    # Parse lexicon
    products = tuple(lexicon_data.get("products", []))
    euphemisms = tuple(lexicon_data.get("euphemisms", []))
    conditions = tuple(lexicon_data.get("conditions", []))
    lexicon = Lexicon(products=products, euphemisms=euphemisms, conditions=conditions)

    # Validate escalation routing has all required categories
    required_categories = {
        "adverse_event",
        "suspected_misuse",
        "distress",
        "pregnancy",
        "clinical_advice",
    }
    routing_categories = {r.get("category") for r in escalation_routing_data}
    missing = required_categories - routing_categories
    if missing:
        raise RulesetValidationError(
            f"escalation_routing missing categories: {missing}"
        )

    # Parse escalation routing
    escalation_routes = []
    for route_data in escalation_routing_data:
        category = route_data.get("category")
        queue = route_data.get("queue")
        value_source = route_data.get("value_source")
        target_response_minutes = route_data.get("target_response_minutes")

        if not isinstance(target_response_minutes, int):
            raise RulesetValidationError(
                f"Route {category}: target_response_minutes must be int, got {type(target_response_minutes)}"
            )

        if value_source != "assumed":
            raise RulesetValidationError(
                f"Route {category}: value_source must be 'assumed', got {value_source}"
            )

        route = EscalationRoute(
            category=category,
            queue=queue,
            target_response_minutes=target_response_minutes,
            value_source=value_source,
        )
        escalation_routes.append(route)

    # Parse rules
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

    # Parse second opinion
    second_opinion_enabled = second_opinion_data.get("enabled", False)

    return Ruleset(
        jurisdiction=jurisdiction,
        version=version,
        rules=tuple(rules),
        lexicon=lexicon,
        escalation_routing=tuple(escalation_routes),
        second_opinion_enabled=second_opinion_enabled,
        fallback_active=False,
        fallback_banner="",
    )


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
    fallback_active = False
    fallback_banner = ""

    if jurisdiction is None:
        # Unset jurisdiction falls back to AU with banner
        jurisdiction = "au"
        fallback_active = True
        fallback_banner = (
            "Note: No explicit jurisdiction specified. "
            "Using AU ruleset as fallback. "
            "Other jurisdictions (UK, NZ) must be explicitly specified."
        )

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

    ruleset = load_ruleset_file(ruleset_file)

    # Apply fallback flag if needed
    if fallback_active:
        import dataclasses

        ruleset = dataclasses.replace(
            ruleset,
            fallback_active=True,
            fallback_banner=fallback_banner,
        )

    return ruleset


def route_for(ruleset: Ruleset, category: str) -> EscalationRoute:
    """Get the escalation route for a given category.

    Args:
        ruleset: The ruleset.
        category: The category name.

    Returns:
        The EscalationRoute for the category.

    Raises:
        KeyError: If the category is not found.
    """
    for route in ruleset.escalation_routing:
        if route.category == category:
            return route
    raise KeyError(f"Category {category} not found in escalation_routing")
