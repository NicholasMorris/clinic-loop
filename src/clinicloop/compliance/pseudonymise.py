"""Per-run HMAC-based pseudonymisation."""


def pseudonymise(value: str, run_key: str) -> str:
    """Generate a stable keyed-HMAC token for a value.

    The token is stable within a run (same key produces same token for same value)
    but differs across runs (different keys produce different tokens).

    Args:
        value: The value to pseudonymise.
        run_key: The run key (generated once per process, never written to disk).

    Returns:
        A pseudonymised token that does not contain 4+ char substrings of the input.
    """
    raise NotImplementedError()


def current_run_key() -> str:
    """Get the current run's HMAC key.

    Generated once per process, never written to disk, discarded at run end.

    Returns:
        The run key for pseudonymisation.
    """
    raise NotImplementedError()
