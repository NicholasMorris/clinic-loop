"""Guard verdict model carrying rule violation information."""

from dataclasses import dataclass


class JurisdictionMismatch(Exception):
    """Raised when ruleset jurisdiction does not match check jurisdiction."""

    pass


@dataclass(frozen=True)
class GuardVerdict:
    """Verdict from a guard check.

    Attributes:
        allowed: True if text passes all rules, False if any rule is violated.
        rule_ids: Tuple of rule ids that were violated (empty if allowed=True).
        jurisdiction: Jurisdiction code the check was performed against.
        ruleset_version: Version of the ruleset used.
        text_sha256: SHA256 hex digest of the text that was checked (UTF-8).
    """

    allowed: bool
    rule_ids: tuple[str, ...]
    jurisdiction: str
    ruleset_version: str
    text_sha256: str
