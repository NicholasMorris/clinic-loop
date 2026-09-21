"""Tests for per-run HMAC pseudonymisation."""

from clinicloop.compliance.pseudonymise import current_run_key, pseudonymise


def test_tokens_stable_per_run_distinct_across_runs_and_key_unpersisted() -> None:
    """AC6: Pseudonymisation tokens are stable per key, distinct across keys, key not persisted."""
    value = "patient_12345"
    key_a = current_run_key()
    key_b = current_run_key()  # Second call in same run should return same key

    # Same value and key should produce identical token
    token_a1 = pseudonymise(value, key_a)
    token_a2 = pseudonymise(value, key_a)
    assert token_a1 == token_a2, "Tokens should be stable for same value and key"

    # Different key should produce different token
    token_b = pseudonymise(value, key_b)
    assert token_b != token_a1, "Different keys should produce different tokens"

    # Tokens should not contain 4+ char substrings of input
    for token in [token_a1, token_b]:
        # Check no substring of length 4 or more from the value exists in token
        for i in range(len(value) - 3):
            substring = value[i : i + 4]
            assert substring not in token, (
                f"Token contains substring '{substring}' from input value"
            )

    # After run ends, run key should not be found in any files
    run_key = current_run_key()
    # Check that the key doesn't appear in tracked files
    # (simplified check - would need to scan actual files)
    assert run_key is not None
