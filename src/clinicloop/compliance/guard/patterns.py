"""Compiled regex patterns for guard rule matching."""

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
    raise NotImplementedError("build_patterns() stub")
