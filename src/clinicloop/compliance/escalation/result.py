"""Escalation detection results and clear tokens."""

from dataclasses import dataclass, field
from typing import Optional


class EscalationClearForbidden(Exception):
    """Raised when EscalationClear is constructed directly."""

    pass


class EscalationRequired(Exception):
    """Raised when draft is called without a matching clear token."""

    pass


@dataclass(frozen=True)
class EvidenceSpan:
    """A single piece of escalation evidence.

    Attributes:
        source: 'rule', 'classifier', or 'error'.
        category: The escalation category or None.
        detail: Description (e.g., rule name, classifier name, error detail).
        start: Start offset in the normalised joined patient text, or None.
        end: End offset in the normalised joined patient text, or None.
    """

    source: str
    category: Optional[str]
    detail: str
    start: Optional[int]
    end: Optional[int]


# Private key for minting EscalationClear tokens
_MINT_KEY = object()


@dataclass(frozen=True)
class EscalationClear:
    """Token indicating a thread has been checked and escalation is not required.

    Can only be constructed by the detector module using a private key.
    Direct construction raises EscalationClearForbidden.

    Attributes:
        text_sha256: SHA-256 hex digest of the thread as json.dumps(thread).
        _key: Private sentinel; must be _MINT_KEY.
    """

    text_sha256: str
    _key: object = field(repr=False, compare=False, default=object())

    def __post_init__(self) -> None:
        """Validate that the token was minted with the correct key."""
        if self._key is not _MINT_KEY:
            raise EscalationClearForbidden(
                "EscalationClear can only be constructed by the detector module"
            )


@dataclass(frozen=True)
class EscalationResult:
    """Result of escalation detection on a thread.

    Attributes:
        category: Escalation category or None; one of
            {'adverse_event', 'suspected_misuse', 'distress', 'pregnancy',
             'clinical_advice', 'detector_error', 'none'}.
        evidence: Tuple of EvidenceSpan showing why this category was chosen.
        queue: Clinician queue name for this category, or None if category is 'none'.
        target_response_minutes: Target response time, or None if category is 'none'.
        clear: EscalationClear token if category is 'none', else None.
        thread_sha256: SHA-256 of the input thread.
    """

    category: str
    evidence: tuple[EvidenceSpan, ...]
    queue: Optional[str]
    target_response_minutes: Optional[int]
    clear: Optional[EscalationClear]
    thread_sha256: str
