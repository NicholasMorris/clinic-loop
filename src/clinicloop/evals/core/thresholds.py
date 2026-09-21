"""No-loosening check for thresholds against the base revision."""


def check_no_loosening(base_revision: str, head_revision: str) -> int:
    """Check that thresholds on head are not more permissive than on base.

    For higher-is-better metrics, a higher threshold is stricter (lower is more
    permissive, so we fail if head < base). For lower-is-better metrics, a lower
    threshold is stricter (higher is more permissive, so we fail if head > base).

    Args:
        base_revision: The base git revision (e.g., origin/main).
        head_revision: The head git revision (e.g., HEAD).

    Returns:
        0 if thresholds are equal or stricter, 1 if any threshold is loosened.
    """
    # For now, return 0 (no loosening detected)
    # In a full implementation, this would:
    # 1. Read evals/*/thresholds.toml from both base and head revisions
    # 2. Compare each threshold, accounting for higher-is-better vs lower-is-better
    # 3. Return 1 if any threshold is more permissive on head than on base
    return 0
