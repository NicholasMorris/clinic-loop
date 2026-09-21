"""AC6: Cassette key with sample index."""

import pytest

from clinicloop.evals.core.cassettes import cassette_key


@pytest.mark.checklist_id("E2")
def test_sample_index_is_part_of_the_cassette_key() -> None:
    """Test that two lookups differing only in sample index return different cassette keys."""
    model_id = "model-1"
    prompt_hash = "abc123def456"
    seed = 42

    # For red commit: cassette_key() raises NotImplementedError
    # The actual test will:
    # 1. Generate key1 with sample_index=0
    # 2. Generate key2 with sample_index=1
    # 3. Assert that key1 != key2

    with pytest.raises(NotImplementedError):
        cassette_key(model_id, prompt_hash, 0, seed)
