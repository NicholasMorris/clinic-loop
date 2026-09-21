"""Conformance tests for M1-6 AgentPort and PortRegistry.

Requirement ID: C0 (SimClinic)
"""

from clinicloop.world.ports import PortRegistry, UnknownAgentScope
from clinicloop.world.ports.fakes import FakeAgentPort


def test_C0_agent_port_protocol_exists() -> None:
    """C0: AgentPort protocol enables agent implementation."""
    from clinicloop.world.ports import AgentPort

    # Verify protocol has required methods
    assert hasattr(AgentPort, "serve"), "AgentPort should have serve method"


def test_C0_port_registry_has_three_scopes() -> None:
    """C0: PortRegistry manages exactly three toggleable scopes."""
    registry = PortRegistry()
    scopes = registry.toggleable_scopes()

    expected = {"triage", "integrity", "consult_documentation"}
    assert scopes == expected, f"Expected {expected}, got {scopes}"


def test_C0_fake_agent_port_available() -> None:
    """C0: FakeAgentPort ships as a test double in src."""
    fake_port = FakeAgentPort(service_time_fraction=0.1)
    assert fake_port is not None

    # Verify it has serve method
    assert callable(getattr(fake_port, "serve", None)), (
        "FakeAgentPort should have callable serve method"
    )


def test_C0_factory_scope_not_toggleable() -> None:
    """C0: Factory is not a toggleable scope; it measures impact instead."""
    registry = PortRegistry()
    scopes = registry.toggleable_scopes()

    assert "factory" not in scopes, (
        "factory should not be in toggleable scopes"
    )

    # Registering factory should raise
    try:
        registry.register("factory", FakeAgentPort(service_time_fraction=0.1))  # type: ignore[arg-type]
        assert False, "Should have raised UnknownAgentScope"
    except UnknownAgentScope:
        pass
