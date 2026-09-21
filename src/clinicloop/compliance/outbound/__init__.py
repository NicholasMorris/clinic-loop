"""Outbound port: sink for guard-checked text."""

from .port import GuardBlocked, GuardMismatch, OutboundPort, StaleRuleset

__all__ = ["OutboundPort", "GuardMismatch", "GuardBlocked", "StaleRuleset"]
