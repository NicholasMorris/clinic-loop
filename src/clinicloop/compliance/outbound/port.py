"""Outbound port: the only code path that calls a transport."""


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

    def __init__(self, transport, ruleset):  # type: ignore[no-untyped-def]
        """Initialize the port.

        Args:
            transport: Callable[[str], None] that sends the text.
            ruleset: Ruleset object with version information.
        """
        self.transport = transport
        self.ruleset = ruleset

    def send(self, text: str, verdict) -> None:  # type: ignore[no-untyped-def]
        """Send text only if verdict is valid and allowed.

        Raises:
            GuardMismatch: If sha256(text) != verdict.text_sha256.
            GuardBlocked: If verdict.allowed is False.
            StaleRuleset: If verdict.ruleset_version != self.ruleset.version.
        """
        raise NotImplementedError("OutboundPort.send() stub")
