"""Match finding for guard rules."""

from dataclasses import dataclass

from .normalise import normalise
from .patterns import build_patterns


@dataclass(frozen=True)
class Match:
    """A match of a rule in normalised text.

    Attributes:
        rule_id: The rule identifier.
        start: Start offset in normalised text (inclusive).
        end: End offset in normalised text (exclusive).
    """

    rule_id: str
    start: int
    end: int


def find_matches(text: str, ruleset) -> list[Match]:  # type: ignore[no-untyped-def]
    """Find all rule matches in text.

    Offsets index the NORMALISED text, not the original text.
    The matched text itself is never returned.

    Args:
        text: The text to search.
        ruleset: The ruleset with rules and lexicon.

    Returns:
        List of Match objects with rule_id and offsets.
    """
    # Normalise the text
    normalised_text = normalise(text)

    # Build patterns
    patterns = build_patterns(ruleset)

    # Find all matches
    matches: list[Match] = []

    for rule in ruleset.rules:
        rule_id = rule.rule_id
        pattern = patterns.get(rule_id)

        if pattern:
            for match_obj in pattern.finditer(normalised_text):
                start, end = match_obj.span()
                matches.append(Match(rule_id=rule_id, start=start, end=end))

    return matches
