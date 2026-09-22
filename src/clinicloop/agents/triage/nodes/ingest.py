"""Ingest node: redact PII and detect language."""


def ingest(state: dict, raw_message: str, run_key: str) -> dict:
    """Redact PII from raw patient message and detect language.

    Args:
        state: Current TriageState as dict (for type flexibility during graph execution).
        raw_message: Raw unredacted patient message.
        run_key: Key for consistent pseudonym hashing within this run.

    Returns:
        State update dict with redacted_thread, patient_data_block, and language.

    Raises:
        NotImplementedError: Until implemented.
    """
    raise NotImplementedError("ingest not yet implemented")
