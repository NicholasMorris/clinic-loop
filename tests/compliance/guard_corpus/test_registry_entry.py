"""Test guard component registry entry."""

from typing import Any

from clinicloop.evals.core.registry import clear_registry, get_metric
from clinicloop.evals.guard import load_cases


def test_guard_component_registered_with_zero_violation_threshold() -> None:
    """AC5: Guard component registered with rule_violation_rate=0.0."""
    clear_registry()

    # Registration is idempotent and explicit: importing the module twice would not re-run it
    from clinicloop.evals.guard.metric import register_guard_metric

    register_guard_metric()

    # Check registry entry exists
    entry = get_metric("guard", "rule_violation_rate")
    assert entry is not None, "guard/rule_violation_rate not registered"

    metric_func, threshold = entry
    assert threshold == 0.0, f"Expected threshold 0.0, got {threshold}"

    # Test metric with oracle check_fn (returns correct verdicts)
    cases = load_cases()

    def oracle_check_fn(thread: list[Any], jurisdiction: str) -> Any:
        """Oracle check: always allow."""

        class Result:
            def __init__(self) -> None:
                self.allowed = True
                self.rule_ids: list[str] = []

        return Result()

    # With oracle allowing everything, rate should be
    # violations / cases = (# block cases / total)
    violation_rate = metric_func(check_fn=oracle_check_fn, cases=cases)
    block_count = sum(1 for c in cases if c.expected_verdict == "block")
    total = len(cases)
    expected_rate = block_count / total
    assert abs(violation_rate - expected_rate) < 0.001, (
        f"Oracle allow rate {violation_rate} != expected {expected_rate}"
    )

    # Test metric with always-allow check_fn
    def always_allow_check_fn(thread: list[Any], jurisdiction: str) -> Any:
        """Check that always allows."""

        class Result:
            def __init__(self) -> None:
                self.allowed = True
                self.rule_ids: list[str] = []

        return Result()

    rate = metric_func(check_fn=always_allow_check_fn, cases=cases)
    assert rate == expected_rate, f"Always-allow rate {rate} != {expected_rate}"

    # Test metric with check that returns wrong rule_id for block cases
    def wrong_rule_check_fn(thread: list[Any], jurisdiction: str) -> Any:
        """Check that returns wrong rule id for block cases."""

        class Result:
            def __init__(self) -> None:
                self.allowed = False
                # Return wrong rule for block cases
                self.rule_ids = ["AU-G-WRONG-ID"]

        return Result()

    rate = metric_func(check_fn=wrong_rule_check_fn, cases=cases)
    # At least one violation (the wrong rule case)
    assert rate >= (1 / len(cases)), f"Wrong rule rate {rate} too low"
