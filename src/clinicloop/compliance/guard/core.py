"""Guard core: pure function check for compliance rules."""

import hashlib
from typing import Any

from .normalise import normalise
from .patterns import build_patterns
from .verdict import GuardVerdict, JurisdictionMismatch


def check(
    thread: list[Any], jurisdiction: str, ruleset: Any, second_opinion: Any = None
) -> GuardVerdict:
    """Check a conversation thread against compliance rules.

    This is a pure function that performs no IO and never mutates its inputs.

    Args:
        thread: List of messages with 'role' and 'text' attributes/keys.
        jurisdiction: Jurisdiction code (e.g., 'au').
        ruleset: Ruleset object with jurisdiction, version, and rules.
        second_opinion: Optional callable that returns list of extra rule ids.

    Returns:
        GuardVerdict with allowed status and rule ids.

    Raises:
        ValueError: If thread has no assistant messages.
        JurisdictionMismatch: If ruleset.jurisdiction != jurisdiction.
    """
    # Check jurisdiction matches
    if ruleset.jurisdiction != jurisdiction:
        ruleset_jur = ruleset.jurisdiction
        msg = (
            f"Ruleset jurisdiction '{ruleset_jur}' does not match "
            f"check jurisdiction '{jurisdiction}'"
        )
        raise JurisdictionMismatch(msg)

    # Extract assistant messages only
    assistant_texts = []
    for message in thread:
        # Handle both dict and object with .role/.text
        if isinstance(message, dict):
            role = message.get("role")
            text = message.get("text", "")
        else:
            role = getattr(message, "role", None)
            text = getattr(message, "text", "")

        if role == "assistant":
            assistant_texts.append(text)

    if not assistant_texts:
        raise ValueError("Thread must have at least one assistant message")

    # Join all assistant messages with a single space
    combined_text = " ".join(assistant_texts)

    # Store the exact text for sha256
    draft_text = combined_text

    # Normalise for matching
    normalised_text = normalise(combined_text)

    # Build patterns from ruleset
    patterns = build_patterns(ruleset)

    # Run all rules and collect violations
    rule_ids_set = set()

    for rule in ruleset.rules:
        rule_id = rule.rule_id
        pattern = patterns.get(rule_id)

        if pattern and pattern.search(normalised_text):
            rule_ids_set.add(rule_id)

    # Apply second opinion if enabled and provided
    if ruleset.second_opinion_enabled and second_opinion is not None:
        extra_rule_ids = second_opinion(thread)
        if extra_rule_ids:
            rule_ids_set.update(extra_rule_ids)

    # Compute SHA256 of the exact draft text (UTF-8)
    text_sha256 = hashlib.sha256(draft_text.encode("utf-8")).hexdigest()

    # Build verdict
    allowed = len(rule_ids_set) == 0
    rule_ids = tuple(sorted(rule_ids_set))

    return GuardVerdict(
        allowed=allowed,
        rule_ids=rule_ids,
        jurisdiction=jurisdiction,
        ruleset_version=ruleset.version,
        text_sha256=text_sha256,
    )
