"""Escalation detection engine."""

import concurrent.futures
import hashlib
import json
from typing import Callable, Optional

from clinicloop.compliance.escalation.result import (
    _MINT_KEY,
    EscalationClear,
    EscalationResult,
    EvidenceSpan,
)
from clinicloop.compliance.escalation.rules import compile_rules
from clinicloop.compliance.guard.normalise import normalise
from clinicloop.compliance.rulesets import Ruleset, RulesetValidationError, route_for


def thread_sha256(thread: list[dict[str, str]]) -> str:
    """Compute SHA-256 of thread as JSON.

    Args:
        thread: List of message dicts.

    Returns:
        SHA-256 hex digest.
    """
    # json.dumps with ensure_ascii=False, separators=(',', ':'), sort_keys=False (preserves order)
    json_str = json.dumps(
        [[m.get("role"), m.get("text")] for m in thread],
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return hashlib.sha256(json_str.encode("utf-8")).hexdigest()


def detect(
    thread: list[dict[str, str]],
    ruleset: Ruleset,
    classifier: Optional[Callable[[list[dict[str, str]]], Optional[str]]] = None,
    timeout_seconds: float = 5.0,
) -> EscalationResult:
    """Detect escalation in a patient thread.

    Args:
        thread: List of message dicts with 'role' and 'text' keys.
        ruleset: The jurisdiction ruleset with escalation_routing.
        classifier: Optional classifier callable returning category or None.
        timeout_seconds: Timeout for classifier execution.

    Returns:
        EscalationResult with category, evidence, queue, target_response_minutes,
        clear, and thread_sha256.

    Raises:
        RulesetValidationError: If escalation_routing is incomplete.
    """
    # Validate ruleset has all required categories in escalation_routing
    routing_categories = {r.category for r in ruleset.escalation_routing}
    required = {"adverse_event", "suspected_misuse", "distress", "pregnancy", "clinical_advice"}
    if required - routing_categories:
        raise RulesetValidationError(
            f"escalation_routing missing categories: {required - routing_categories}"
        )

    # Compute thread hash for clear token
    thread_hash = thread_sha256(thread)

    # Extract and normalize patient text (join all patient messages)
    patient_text = " ".join(m.get("text", "") for m in thread if m.get("role") == "patient")
    normalized_text = normalise(patient_text)

    # Compile rules and check for matches
    rules = compile_rules()
    evidence: list[EvidenceSpan] = []
    rule_categories: dict[str, EvidenceSpan] = {}

    # Check each rule in priority order
    priority_order = [
        "distress",
        "adverse_event",
        "pregnancy",
        "suspected_misuse",
        "clinical_advice",
    ]

    for category in priority_order:
        rule = getattr(rules, category)
        matches = list(rule.finditer(normalized_text))
        if matches:
            for match in matches:
                span = EvidenceSpan(
                    source="rule",
                    category=category,
                    detail=f"Pattern match: {category}",
                    start=match.start(),
                    end=match.end(),
                )
                evidence.append(span)
                if category not in rule_categories:
                    rule_categories[category] = span

    # Run classifier if provided
    classifier_category: Optional[str] = None
    classifier_evidence: list[EvidenceSpan] = []

    if classifier is not None:
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(classifier, thread)
                try:
                    classifier_category = future.result(timeout=timeout_seconds)
                except concurrent.futures.TimeoutError:
                    classifier_evidence.append(
                        EvidenceSpan(
                            source="error",
                            category=None,
                            detail=f"classifier timeout after {timeout_seconds}s",
                            start=None,
                            end=None,
                        )
                    )
                    classifier_category = None
                finally:
                    executor.shutdown(wait=False, cancel_futures=True)
        except Exception as e:
            classifier_evidence.append(
                EvidenceSpan(
                    source="error",
                    category=None,
                    detail=f"classifier error: {type(e).__name__}: {str(e)}",
                    start=None,
                    end=None,
                )
            )
            classifier_category = None

        if classifier_evidence:
            evidence.extend(classifier_evidence)

    # Determine final category by priority
    final_category: Optional[str] = None
    error_evidence = [e for e in evidence if e.source == "error"]

    if rule_categories or classifier_category:
        # Collect all categories from rules and classifier
        all_categories = set(rule_categories.keys())
        if classifier_category:
            all_categories.add(classifier_category)

        # If classifier returned unknown category, treat as error
        if classifier_category and classifier_category not in priority_order:
            if not error_evidence:
                evidence.append(
                    EvidenceSpan(
                        source="error",
                        category=None,
                        detail=f"classifier returned unknown category: {classifier_category}",
                        start=None,
                        end=None,
                    )
                )

        # Use priority order to pick final category
        for cat in priority_order:
            if cat in all_categories:
                final_category = cat
                break

        # If only unknown classifier categories and no rules, it's detector_error
        if final_category is None and all_categories:
            final_category = "detector_error"

    # If classifier errored/timed out but no rule/valid classifier match, escalate
    if final_category is None and classifier_evidence:
        final_category = "detector_error"

    # If still no category, it's 'none'
    if final_category is None:
        final_category = "none"

    # Get routing info
    queue: Optional[str] = None
    target_response_minutes: Optional[int] = None
    clear: Optional[EscalationClear] = None

    if final_category == "none":
        # Mint clear token
        clear = EscalationClear(text_sha256=thread_hash, _key=_MINT_KEY)
    elif final_category == "detector_error":
        # Use the route with the smallest target_response_minutes (fail safe)
        fastest_route = min(ruleset.escalation_routing, key=lambda r: r.target_response_minutes)
        queue = fastest_route.queue
        target_response_minutes = fastest_route.target_response_minutes
    else:
        # Look up routing
        route = route_for(ruleset, final_category)
        queue = route.queue
        target_response_minutes = route.target_response_minutes

    return EscalationResult(
        category=final_category,
        evidence=tuple(evidence),
        queue=queue,
        target_response_minutes=target_response_minutes,
        clear=clear,
        thread_sha256=thread_hash,
    )
