"""AC3: Recompute script with staleness detection."""

import tempfile
from pathlib import Path

import pytest

from clinicloop.evals.core.recompute import recompute


@pytest.mark.checklist_id("E2")
def test_recompute_fails_on_mismatched_aggregate() -> None:
    """Test that recompute exits 1 when committed aggregate differs from recomputed value."""
    with tempfile.TemporaryDirectory() as tmpdir:
        results_dir = Path(tmpdir) / "results"
        results_dir.mkdir()

        # For red commit: recompute() raises NotImplementedError
        with pytest.raises(NotImplementedError):
            recompute(results_dir)
