"""Guard evaluation metric: rule_violation_rate."""

from typing import Callable

from clinicloop.evals.core.registry import get_metric, register_metric

from .corpus_loader import load_cases


def rule_violation_rate(
    check_fn: Callable, cases: list | None = None
) -> float:
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

        Raises:
        NotImplementedError: Stub not yet implemented.
    """
    raise NotImplementedError("rule_violation_rate stub")


def register_guard_metric() -> None:
    """Register the guard metric in the eval registry.

    Idempotent: if already registered, skips.
    """
    if get_metric("guard", "rule_violation_rate") is not None:
        return

    # Read threshold from evals/guard/thresholds.toml
    import tomllib
    from pathlib import Path

    thresholds_path = (
        Path(__file__).resolve().parents[4] / "evals" / "guard" / "thresholds.toml"
    )
    with open(thresholds_path, "rb") as f:
        config = tomllib.load(f)

    threshold = config.get("rule_violation_rate", 0.0)

    register_metric("guard", "rule_violation_rate", rule_violation_rate, threshold)


# Register on import
register_guard_metric()
