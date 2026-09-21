"""Decoy module for testing boundary scanner.

This module exists only to be scanned by test_boundaries.py
to verify the scanner detects forbidden symbols.
DO NOT import this in any actual code.
"""


class SignoffService:
    """A decoy class that should trigger boundary scanner violations."""

    def sign(self, note_hash: str) -> None:
        """A forbidden method."""
        pass
