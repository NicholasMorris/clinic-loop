"""PII redaction with nine identifier classes and checksum validators."""

from typing import Callable


def redact(text: str) -> str:
    """Remove PII identifiers from text.

    Redacts nine identifier classes:
    - National health number (Medicare/Medicare levy levy)
    - Tax identifier (TFN in AU)
    - Phone number
    - Email address
    - Date of birth
    - Street address
    - NZ health index (NHI)
    - UK health number (NHS)
    - Synthetic-roster name matcher

    Args:
        text: Text potentially containing PII.

    Returns:
        Text with PII redacted.
    """
    raise NotImplementedError()
