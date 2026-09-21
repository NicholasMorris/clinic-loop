"""Test no-loosening check for thresholds."""

import os
from pathlib import Path

from clinicloop.evals.core.thresholds import check_no_loosening


def test_raising_guard_threshold_above_zero_fails_the_check(tmp_path: Path) -> None:
    """AC6: Raising rule_violation_rate to 0.01 fails; unchanged passes."""
    # Create stub reader for prior threshold at 0.0
    prior_toml = """rule_violation_rate = 0.0
# Must never be raised above zero
"""

    # Create stub reader for current threshold at 0.01 (loosened)
    current_toml_loosened = """rule_violation_rate = 0.01
# Accidentally raised
"""

    def reader_loosened(revision: str, path: str) -> str | None:
        """Reader: prior has 0.0, current has 0.01 (loosened)."""
        if path == "evals/guard/thresholds.toml":
            if revision == "origin/main":
                return prior_toml
            else:
                return current_toml_loosened
        return None

    # Create the directory structure and file in tmp_path
    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)

        # Create evals/guard/ directory and thresholds file
        evals_dir = tmp_path / "evals" / "guard"
        evals_dir.mkdir(parents=True)
        thresholds_file = evals_dir / "thresholds.toml"
        thresholds_file.write_text(current_toml_loosened)

        # Should fail (return 1)
        exit_code = check_no_loosening("origin/main", "HEAD", reader=reader_loosened)
        assert exit_code == 1, f"Expected exit code 1 for loosened threshold, got {exit_code}"

        # Test unchanged (should pass)
        thresholds_file.write_text(prior_toml)

        def reader_unchanged(revision: str, path: str) -> str | None:
            """Reader: both prior and current at 0.0 (unchanged)."""
            if path == "evals/guard/thresholds.toml":
                return prior_toml
            return None

        exit_code = check_no_loosening("origin/main", "HEAD", reader=reader_unchanged)
        assert exit_code == 0, f"Expected exit code 0 for unchanged, got {exit_code}"
    finally:
        os.chdir(original_cwd)
