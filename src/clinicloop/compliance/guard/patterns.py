"""Compiled regex patterns for guard rule matching."""

import re
from functools import lru_cache


@lru_cache(maxsize=8)
def build_patterns(ruleset):  # type: ignore[no-untyped-def]
    """Build compiled regex patterns from ruleset.

    Caches patterns based on the hashable ruleset.

    Args:
        ruleset: Ruleset object with lexicon and rules.

    Returns:
        Dictionary of compiled patterns for each rule type.
    """
    patterns = {}

    # PRODUCT: Rx-only product name (brand or generic)
    # Alternation with word boundaries
    if ruleset.lexicon.products:
        product_pattern = "|".join(re.escape(p) for p in ruleset.lexicon.products)
        patterns["AU-G-PRODUCT"] = re.compile(f"(?<![a-z])({product_pattern})(?![a-z])")
    else:
        patterns["AU-G-PRODUCT"] = re.compile(r"(?!)")  # Never match

    # EUPHEMISM: Product euphemism phrases (substring match)
    if ruleset.lexicon.euphemisms:
        euphemism_pattern = "|".join(re.escape(e) for e in ruleset.lexicon.euphemisms)
        patterns["AU-G-EUPHEMISM"] = re.compile(euphemism_pattern)
    else:
        patterns["AU-G-EUPHEMISM"] = re.compile(r"(?!)")  # Never match

    # DOSE: Number with unit (may be split across messages)
    # Units: mg, mcg, ug, µg, g, ml, iu, units, tablet, tablets, tab, tabs,
    # capsule, capsules, pill, pills
    units = (
        r"(?:mg|mcg|ug|µg|g|ml|iu|units|tablet|tablets|tab|tabs|"
        r"capsule|capsules|pill|pills)"
    )
    patterns["AU-G-DOSE"] = re.compile(r"\d+(?:\.\d+)?\s?" + units)

    # CONDITION: Condition claim pattern
    # Pattern 1: "you have|you've got|you are suffering from|..." followed
    # within 6 words by condition
    # Pattern 2: "cures|treats|will fix|..." followed within 6 words by condition
    if ruleset.lexicon.conditions:
        condition_pattern = "|".join(re.escape(c) for c in ruleset.lexicon.conditions)

        # You-have pattern: You have/have got/suffer from... + condition within 6 words
        # Include contractions like "you've" which may have an apostrophe
        have_pattern = (
            r"(?:you\s+have|you[\'']ve\s+got|you\s+have\s+got|youve\s+got|you\s+are\s+suffering\s+from|"
            r"you\s+suffer\s+from|you\s+are\s+diagnosed\s+with|"
            r"you\s+clearly\s+have|you\s+definitely\s+have)"
            r"(?:\s+\S+){0,5}\s+(?:" + condition_pattern + r")"
        )

        # Cures pattern: cures/treats/will fix/... + condition within 6 words
        cure_pattern = (
            r"(?:cures|treats|will\s+fix|will\s+heal|is\s+guaranteed\s+to\s+(?:help|cure))"
            r"(?:\s+\S+){0,5}\s+(?:" + condition_pattern + r")"
        )

        patterns["AU-G-CONDITION"] = re.compile(f"({have_pattern}|{cure_pattern})")
    else:
        patterns["AU-G-CONDITION"] = re.compile(r"(?!)")  # Never match

    # ADVICE: Clinical advice pattern
    advice_phrases = (
        r"(?:you\s+should\s+(?:take|stop|start|increase|decrease|combine|skip)|"
        r"it\s+is\s+safe\s+to|it's\s+safe\s+to|safe\s+to\s+combine|stop\s+taking|"
        r"increase\s+your|decrease\s+your|double\s+up|skip\s+your)"
    )
    patterns["AU-G-ADVICE"] = re.compile(advice_phrases)

    return patterns
