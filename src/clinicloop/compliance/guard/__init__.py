"""Guard core: pure function check and verdict types."""

from .core import check
from .verdict import GuardVerdict, JurisdictionMismatch

__all__ = ["check", "GuardVerdict", "JurisdictionMismatch"]
