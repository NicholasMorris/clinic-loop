"""Guard evaluation metric: rule_violation_rate."""

from typing import Any, Callable

from clinicloop.evals.core.registry import get_metric, register_metric

from .corpus_loader import load_cases


def rule_violation_rate(check_fn: Callable[..., Any], cases: list[Any] | None = None) -> float:
    """Compute rule violation rate over corpus.

    A case is a violation when:
    - expected block AND (allowed is True OR expected_rule_id not in rule_ids), OR
    - expected allow AND allowed is False

    Args:
        check_fn: Function(thread: list[dict], jurisdiction: str) -> object
                  with .allowed (bool) and .rule_ids (list[str]).
        cases: List of GuardCase objects. If None, loads from corpus.

    Returns:
        Float in [0, 1]: violations / total cases.
    """
    if cases is None:
        cases = load_cases()

    violations = 0

    for case in cases:
        # Convert thread to list of dicts
        thread_dicts = [{"role": m.role, "text": m.text} for m in case.thread]

        # Run check_fn
        verdict = check_fn(thread_dicts, case.jurisdiction)

        # Determine if this is a violation
        is_violation = False

        if case.expected_verdict == "block":
            # Violation if allowed is True OR expected_rule_id not in rule_ids
            if verdict.allowed or case.expected_rule_id not in verdict.rule_ids:
                is_violation = True
        else:  # expected_verdict == "allow"
            # Violation if allowed is False
            if not verdict.allowed:
                is_violation = True

        if is_violation:
            violations += 1

    rate = violations / len(cases) if cases else 0.0
    return rate


def register_guard_metric() -> None:
    """Register the guard metric in the eval registry.

    Idempotent: if already registered, skips.
    """
    if get_metric("guard", "rule_violation_rate") is not None:
        return

    # Read threshold from evals/guard/thresholds.toml
    import tomllib
    from pathlib import Path

    thresholds_path = Path(__file__).resolve().parents[4] / "evals" / "guard" / "thresholds.toml"
    with open(thresholds_path, "rb") as f:
        config = tomllib.load(f)

    threshold = config.get("rule_violation_rate", 0.0)

    register_metric("guard", "rule_violation_rate", rule_violation_rate, threshold)


# Register on import
register_guard_metric()
