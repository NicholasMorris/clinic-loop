"""PortRegistry for managing toggleable agent scopes."""

from dataclasses import dataclass
from typing import Any

from clinicloop.world.ports.protocol import AgentPort


class UnknownAgentScope(Exception):
    """Raised when a port is registered under an unknown scope.

    Attributes:
        scope: The unknown scope name.
    """

    def __init__(self, scope: str) -> None:
        """Initialize the exception.

        Args:
            scope: The unknown scope name.
        """
        self.scope = scope
        super().__init__(f"Unknown agent scope: {scope}")


@dataclass
class PortFailure:
    """Record of a port failure (exception during serve).

    Attributes:
        scope: The toggleable scope (triage, integrity, consult_documentation).
        exception_type: Name of the exception class that was raised.
        case_id: The case that triggered the failure.
    """

    scope: str
    exception_type: str
    case_id: str


class PortRegistry:
    """Registry for agent ports on toggleable scopes.

    Exactly three scopes are toggleable: triage, integrity, and
    consult_documentation. Each scope can have zero or one port registered.
    The Factory is not toggleable; it measures impact instead of toggling.

    Ports can be enabled or disabled at runtime, affecting which worker pool
    (agent or human) serves cases starting at that moment. Cases already in
    service when the toggle fires complete on the side they started.
    """

    TOGGLEABLE_SCOPES = {"triage", "integrity", "consult_documentation"}

    def __init__(self) -> None:
        """Initialize an empty registry."""
        self._ports: dict[str, AgentPort] = {}

    def toggleable_scopes(self) -> set[str]:
        """Return the set of toggleable scopes.

        Returns:
            Set of scope names: {"triage", "integrity", "consult_documentation"}.
        """
        return self.TOGGLEABLE_SCOPES.copy()

    def register(self, scope: str, port: AgentPort) -> None:
        """Register an agent port under a scope.

        Args:
            scope: Scope name (must be in toggleable_scopes()).
            port: Object implementing AgentPort protocol.

        Raises:
            UnknownAgentScope: If scope is not in toggleable_scopes().
        """
        if scope not in self.TOGGLEABLE_SCOPES:
            raise UnknownAgentScope(scope)
        self._ports[scope] = port

    def get(self, scope: str) -> AgentPort | None:
        """Get the registered port for a scope, if any.

        Args:
            scope: Scope name.

        Returns:
            The registered AgentPort, or None if no port is registered.
        """
        return self._ports.get(scope)

    def registered_scopes(self) -> set[str]:
        """Return the set of scopes with registered ports.

        Returns:
            Set of scope names that have ports registered.
        """
        return set(self._ports.keys())
