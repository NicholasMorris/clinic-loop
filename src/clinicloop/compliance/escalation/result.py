"""Escalation detection results and clear tokens."""

import hashlib
import hmac
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


class EscalationClearForbidden(Exception):
    """Raised when EscalationClear is constructed with an invalid MAC."""

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


def _key() -> bytes:
    """Get or create the HMAC key for escalation tokens.

    Reads from CLINICLOOP_ESCALATION_KEY env var (as hex) if set.
    Otherwise reads or creates var/keys/escalation.key (32 random bytes as hex).

    Returns:
        32 bytes of key material.

    Raises:
        OSError: If key file cannot be created/read.
    """
    # Check environment variable first
    env_key = os.environ.get("CLINICLOOP_ESCALATION_KEY")
    if env_key:
        return bytes.fromhex(env_key)

    # Otherwise use file-based key
    key_path = Path.cwd() / "var" / "keys" / "escalation.key"
    if key_path.exists():
        with open(key_path, "r") as f:
            return bytes.fromhex(f.read().strip())

    # Create new key
    key_path.parent.mkdir(parents=True, exist_ok=True)
    key_bytes = os.urandom(32)
    key_hex = key_bytes.hex()
    with open(key_path, "w") as f:
        f.write(key_hex)
    key_path.chmod(0o600)
    return key_bytes


@dataclass(frozen=True)
class EscalationClear:
    """Token indicating a thread has been checked and escalation is not required.

    The token is plain data with an HMAC authentication code. It can be serialized,
    restored in a new process on the same machine, and verified against accidental
    or model-driven forgery. It is not a security boundary against a local attacker
    who can read the key file.

    Attributes:
        text_sha256: SHA-256 hex digest of the thread as json.dumps(thread).
        mac: HMAC-SHA256 hex digest of text_sha256 using the machine key.
    """

    text_sha256: str
    mac: str

    def __post_init__(self) -> None:
        """Validate that the MAC is correct for this text_sha256."""
        expected_mac = hmac.new(_key(), self.text_sha256.encode(), hashlib.sha256).hexdigest()
        if self.mac != expected_mac:
            raise EscalationClearForbidden(
                f"EscalationClear MAC mismatch: expected {expected_mac[:16]}..., "
                f"got {self.mac[:16]}..."
            )


def _mint_clear(text_sha256: str) -> EscalationClear:
    """Mint an EscalationClear token (detector-only function).

    Args:
        text_sha256: The SHA-256 digest of the thread.

    Returns:
        A new EscalationClear with the correct MAC.
    """
    mac = hmac.new(_key(), text_sha256.encode(), hashlib.sha256).hexdigest()
    return EscalationClear(text_sha256=text_sha256, mac=mac)


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
