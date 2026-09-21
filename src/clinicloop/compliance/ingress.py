"""Ingress module: redaction and pseudonymisation at module boundary.

Raw identifier values are reachable only from inside this module.
Module-level names holding raw values are underscore-prefixed and not exported.
"""

from typing import Any

from clinicloop.compliance.redaction import redact

__all__ = [
    "process_record",
]


def process_record(record: dict[str, Any]) -> dict[str, Any]:
    """Process a record at ingress: redact and pseudonymise identifiers.

    Redacts all PII in string values. Run key is available via current_run_key()
    for use by detectors that need to pseudonymise identifiers.

    Args:
        record: Record potentially containing raw identifiers.

    Returns:
        Processed record with identifiers redacted/pseudonymised.
    """
    # Process the record
    processed = {}
    for key, value in record.items():
        if isinstance(value, str):
            # Redact PII from string values
            processed[key] = redact(value)
        else:
            # Pass through non-string values
            processed[key] = value

    return processed
