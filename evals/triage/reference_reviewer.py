"""Rule-based reference reviewer for triage drafts."""

from dataclasses import dataclass
from typing import Optional

from evals.triage.golden.loader import IntentElements, load_intent_elements


@dataclass(frozen=True)
class ReviewResult:
    """Result of reviewing a draft.

    Attributes:
        accepted: True if the draft is accepted.
        reason: Reason for rejection, or None if accepted. One of:
            'guard_blocked', 'dose_or_product_match', 'missing_required_element',
            'over_max_chars', or None.
    """

    accepted: bool
    reason: Optional[str] = None


def review(
    draft: str,
    guard_verdict,
    intent: str,
    elements: Optional[IntentElements] = None,
    ruleset=None,
) -> ReviewResult:
    """Review a draft against four rules in priority order.

    Rules (in order):
    1. Guard verdict must allow (guard_blocked).
    2. Draft must not match dose/product patterns (dose_or_product_match).
    3. Draft must contain a required element for the intent (missing_required_element).
    4. Draft must not exceed max_draft_chars (over_max_chars).

    Args:
        draft: The draft text to review.
        guard_verdict: GuardVerdict object with allowed and rule_ids.
        intent: The intent label for this draft.
        elements: IntentElements config. If None, loads from default location.
        ruleset: Ruleset object for finding dose/product matches.

    Returns:
        ReviewResult with accepted status and reason.

    Raises:
        ConfigurationError: If elements cannot be loaded.
    """
    if elements is None:
        elements = load_intent_elements()

    raise NotImplementedError("review not yet implemented")
