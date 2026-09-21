"""No-loosening check for thresholds against the base revision."""

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from clinicloop.evals.core.gitread import git_show

GitReader = Callable[[str, str], str | None]


@dataclass
class NoLooseningResult:
    """Result of a no-loosening check.

    Attributes:
        first_baseline: True if base revision had no thresholds.
        loosened: List of entries that were loosened (component.key).
    """

    first_baseline: bool
    loosened: list[str]


def compare_thresholds(
    component: str, prior_text: str | None, current_text: str
) -> NoLooseningResult:
    """Compare threshold values between prior and current.

    Args:
        component: Component name (e.g., "guard").
        prior_text: Prior threshold text (toml). If None, this is first baseline.
        current_text: Current threshold text (toml).

    Returns:
        NoLooseningResult with first_baseline and loosened list.
    """
    import tomllib

    if prior_text is None:
        # First baseline: no prior thresholds
        return NoLooseningResult(first_baseline=True, loosened=[])

    try:
        prior = tomllib.loads(prior_text)
    except Exception:
        prior = {}

    try:
        current = tomllib.loads(current_text)
    except Exception:
        current = {}

    loosened = []

    for key, current_val in current.items():
        if key not in prior:
            # New key: not a loosening
            continue

        prior_val = prior[key]

        # Skip non-numeric values
        if not isinstance(current_val, (int, float)) or not isinstance(prior_val, (int, float)):
            continue

        # Determine direction: lower is better (loosened if current > prior)
        if "rate" in key or key.startswith("max_") or "_max_" in key:
            # Lower is better
            if current_val > prior_val:
                loosened.append(f"{component}.{key}")
        # Higher is better (min_ keys)
        elif "min" in key:
            if current_val < prior_val:
                loosened.append(f"{component}.{key}")
        else:
            # Loosened if different (conservative: any change is loosening)
            if current_val != prior_val:
                loosened.append(f"{component}.{key}")

    return NoLooseningResult(first_baseline=False, loosened=loosened)


def check_no_loosening(
    base_revision: str, head_revision: str, reader: GitReader | None = None
) -> int:
    """Check that thresholds on head are not more permissive than on base.

    For higher-is-better metrics, a higher threshold is stricter (lower is more
    permissive, so we fail if head < base). For lower-is-better metrics, a lower
    threshold is stricter (higher is more permissive, so we fail if head > base).

    Args:
        base_revision: The base git revision (e.g., origin/main).
        head_revision: The head git revision (e.g., HEAD).
        reader: GitReader function (default git_show).

    Returns:
        0 if thresholds are equal or stricter, 1 if any threshold is loosened.
    """
    if reader is None:
        reader = git_show

    # Find all evals/*/thresholds.toml files in the working tree
    evals_dir = Path("evals")
    loosened_all = []

    if not evals_dir.exists():
        # No evals directory; first baseline
        return 0

    for component_dir in evals_dir.iterdir():
        if not component_dir.is_dir():
            continue

        thresholds_path = component_dir / "thresholds.toml"
        if not thresholds_path.exists():
            continue

        relative_path = str(thresholds_path)
        # Head side comes from the head revision; the working-tree file is only a fallback
        # for a threshold file that is not committed yet.
        current_text = reader(head_revision, relative_path)
        if current_text is None:
            current_text = thresholds_path.read_text()
        prior_text = reader(base_revision, relative_path)

        component = component_dir.name
        result = compare_thresholds(component, prior_text, current_text)

        if result.loosened:
            loosened_all.extend(result.loosened)
            for entry in result.loosened:
                print(f"Loosened: {entry}")

    return 1 if loosened_all else 0


if __name__ == "__main__":
    import sys

    base = sys.argv[1] if len(sys.argv) > 1 else "origin/main"
    head = sys.argv[2] if len(sys.argv) > 2 else "HEAD"

    exit_code = check_no_loosening(base, head)
    sys.exit(exit_code)
