"""AC6: Cassette key with sample index."""

import pytest

from clinicloop.evals.core.cassettes import cassette_key


@pytest.mark.checklist_id("E2")
def test_sample_index_is_part_of_the_cassette_key() -> None:
    """Test that two lookups differing only in sample index return different cassette keys."""
    model_id = "model-1"
    prompt_hash = "abc123def456"
    seed = 42

    # Generate two keys with different sample indices
    first = cassette_key(model_id, prompt_hash, 0, seed)
    second = cassette_key(model_id, prompt_hash, 1, seed)

    # They should be different because sample_index is part of the key
    assert first != second

    # But if we change it back, they should match
    third = cassette_key(model_id, prompt_hash, 0, seed)
    assert first == third
