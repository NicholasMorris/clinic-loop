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

    # Rule 1: Guard verdict must allow
    if not guard_verdict.allowed:
        return ReviewResult(accepted=False, reason="guard_blocked")

    # Rule 2: Draft must not match dose or product patterns
    if ruleset is not None:
        from clinicloop.compliance.guard.matches import find_matches

        matches = find_matches(draft, ruleset)
        # Check for AU-G-PRODUCT or AU-G-DOSE matches
        for match in matches:
            if match.rule_id in ("AU-G-PRODUCT", "AU-G-DOSE"):
                return ReviewResult(accepted=False, reason="dose_or_product_match")

    # Rule 3: Draft must contain a required element for the intent
    if intent in elements.elements:
        required_elements = elements.elements[intent]
        draft_lower = draft.lower()
        has_element = any(elem.lower() in draft_lower for elem in required_elements)
        if not has_element:
            return ReviewResult(accepted=False, reason="missing_required_element")

    # Rule 4: Draft must not exceed max_draft_chars
    if len(draft) > elements.max_draft_chars:
        return ReviewResult(accepted=False, reason="over_max_chars")

    # All checks passed
    return ReviewResult(accepted=True, reason=None)
