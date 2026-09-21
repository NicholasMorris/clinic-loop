"""Outbound port: the only code path that calls a transport."""

import hashlib
from typing import Any, Callable


class GuardMismatch(Exception):
    """Raised when verdict text_sha256 does not match the text being sent."""

    pass


class GuardBlocked(Exception):
    """Raised when verdict.allowed is False."""

    pass


class StaleRuleset(Exception):
    """Raised when verdict.ruleset_version differs from loaded ruleset version."""

    pass


class OutboundPort:
    """Port for sending guard-checked text.

    Only code path that calls the transport; enforces guard verdict integrity.
    """

    def __init__(self, transport: Callable[[str], None], ruleset: Any) -> None:
        """Initialize the port.

        Args:
            transport: Callable[[str], None] that sends the text.
            ruleset: Ruleset object with version information.
        """
        self.transport = transport
        self.ruleset = ruleset

    def send(self, text: str, verdict: Any) -> None:
        """Send text only if verdict is valid and allowed.

        Raises:
            GuardMismatch: If sha256(text) != verdict.text_sha256.
            GuardBlocked: If verdict.allowed is False.
            StaleRuleset: If verdict.ruleset_version != self.ruleset.version.
        """
        # Check 1: Verify sha256 matches
        text_sha256 = hashlib.sha256(text.encode("utf-8")).hexdigest()
        if text_sha256 != verdict.text_sha256:
            raise GuardMismatch(
                f"SHA256 mismatch: computed {text_sha256}, verdict has {verdict.text_sha256}"
            )

        # Check 2: Verify verdict is allowed
        if not verdict.allowed:
            msg = f"Text blocked by rules: {verdict.rule_ids}"
            raise GuardBlocked(msg)

        # Check 3: Verify ruleset version matches
        if verdict.ruleset_version != self.ruleset.version:
            raise StaleRuleset(
                f"Ruleset version mismatch: verdict has {verdict.ruleset_version}, "
                f"loaded ruleset has {self.ruleset.version}"
            )

        # All checks passed: send the text
        self.transport(text)
