"""Agent ports for SimClinic integration.

This module defines the protocol for plugging agents into the simulation
engine, a registry for managing toggleable agent scopes, and a shipped
test double (FakeAgentPort) that real adapters replace.
"""

from clinicloop.world.ports.protocol import AgentPort
from clinicloop.world.ports.registry import PortRegistry, UnknownAgentScope, PortFailure

__all__ = [
    "AgentPort",
    "PortRegistry",
    "UnknownAgentScope",
    "PortFailure",
]
