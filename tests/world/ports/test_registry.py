"""Tests for the PortRegistry and toggleable scopes."""

from clinicloop.world.ports import PortRegistry, UnknownAgentScope


def test_exactly_three_toggleable_scopes() -> None:
    """AC1: port_registry.toggleable_scopes() returns exactly three scopes.

    The three toggleable scopes are: triage, integrity, consult_documentation.
    """
    registry = PortRegistry()
    scopes = registry.toggleable_scopes()
    assert scopes == {"triage", "integrity", "consult_documentation"}


def test_registering_unknown_scope_raises() -> None:
    """AC1: Registering a port under an unknown scope raises UnknownAgentScope."""
    import pytest

    class FakePort:
        """Placeholder port."""

        def serve(self, case_id: str) -> float:
            """Placeholder serve method."""
            raise NotImplementedError

    registry = PortRegistry()
    fake_port = FakePort()

    with pytest.raises(UnknownAgentScope):
        registry.register("factory", fake_port)


def test_factory_has_no_toggleable_port() -> None:
    """AC6: 'factory' scope has no toggleable port.

    toggleable_scopes() does not contain 'factory'.
    register('factory', port) raises UnknownAgentScope.
    """
    import pytest

    registry = PortRegistry()
    scopes = registry.toggleable_scopes()
    assert "factory" not in scopes

    class FakePort:
        """Placeholder port."""

        def serve(self, case_id: str) -> float:
            """Placeholder serve method."""
            raise NotImplementedError

    fake_port = FakePort()

    with pytest.raises(UnknownAgentScope):
        registry.register("factory", fake_port)
