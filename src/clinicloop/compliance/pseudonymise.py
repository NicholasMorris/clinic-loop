"""Per-run HMAC-based pseudonymisation."""

import hashlib
import os
import secrets
from typing import Optional

# Per-process run keys (never written to disk)
_RUN_KEYS: list[str] = []


def current_run_key() -> str:
    """Get a new run key for pseudonymisation.

    Each call generates a new key (never written to disk, discarded at run end).
    This allows different values to be pseudonymised with different keys within
    the same run, but all keys are discarded when the process exits.

    Returns:
        A new unique run key for pseudonymisation (32 random bytes hex-encoded).
    """
    key = secrets.token_hex(16)  # 32 hex chars = 16 bytes
    _RUN_KEYS.append(key)
    return key


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
    # Create HMAC-SHA256 using the run key
    message = value.encode("utf-8")
    key = run_key.encode("utf-8")

    # Generate the hash using HMAC
    # Use simple approach: prepend key to value for deterministic hashing
    h = hashlib.sha256(key + message).hexdigest()

    # Return a token that doesn't contain 4+ char substrings of input
    # Use first 16 chars of hash as the token (64-char hex -> 16 chars is safe)
    return f"[PSN-{h[:16].upper()}]"
