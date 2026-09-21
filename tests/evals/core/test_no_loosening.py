"""AC4: No-loosening check against base revision."""

import pytest

from clinicloop.evals.core.thresholds import check_no_loosening


@pytest.mark.checklist_id("E2")
def test_loosened_threshold_fails_in_both_directions() -> None:
    """Test that loosened thresholds fail in both higher-is-better and lower-is-better directions."""
    # For the red commit, check_no_loosening() raises NotImplementedError
    # The actual test will:
    # 1. Set up a git repo with thresholds on base and head
    # 2. Test higher-is-better metric: if head < base (more permissive), should fail
    # 3. Test lower-is-better metric: if head > base (more permissive), should fail

    with pytest.raises(NotImplementedError):
        check_no_loosening("origin/main", "HEAD")
