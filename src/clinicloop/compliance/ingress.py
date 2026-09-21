"""Ingress module: redaction and pseudonymisation at module boundary.

Raw identifier values are reachable only from inside this module.
Module-level names holding raw values are underscore-prefixed and not exported.
"""

from typing import Any

__all__ = [
    "process_record",
]


def process_record(record: dict[str, Any]) -> dict[str, Any]:
    """Process a record at ingress: redact and pseudonymise identifiers.

    Args:
        record: Record potentially containing raw identifiers.

    Returns:
        Processed record with identifiers redacted/pseudonymised.
    """
    raise NotImplementedError()
