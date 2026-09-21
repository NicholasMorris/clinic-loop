"""Tests for FakeAgentPort as a shipped package member."""

import importlib.util
from pathlib import Path

from clinicloop.world.ports import AgentPort
from clinicloop.world.ports.fakes import FakeAgentPort


def test_fake_agent_port_ships_in_src() -> None:
    """AC7: FakeAgentPort ships in src, not in the test tree.

    - FakeAgentPort imports from clinicloop.world.ports.fakes
    - isinstance(FakeAgentPort(service_time_fraction=0.1), AgentPort) is True
    - No imports from 'tests' module found in src/clinicloop/world/ports/
    """
    # Verify FakeAgentPort is importable from the shipped location
    from clinicloop.world.ports.fakes import FakeAgentPort as FakePort

    assert FakePort is not None

    # Verify it implements AgentPort protocol
    instance = FakePort(service_time_fraction=0.1)
    assert isinstance(instance, AgentPort), (
        f"FakeAgentPort should be an instance of AgentPort protocol, "
        f"got {type(instance)}"
    )

    # Scan src/clinicloop/world/ports for test imports
    ports_dir = Path(__file__).parent.parent.parent.parent / "src" / "clinicloop" / "world" / "ports"
    assert ports_dir.exists(), f"Expected ports directory at {ports_dir}"

    for py_file in ports_dir.glob("**/*.py"):
        with open(py_file) as f:
            content = f.read()
            assert "from tests" not in content, (
                f"File {py_file} imports from tests module, "
                "which violates src-only requirement"
            )
            assert "import tests" not in content, (
                f"File {py_file} imports from tests module, "
                "which violates src-only requirement"
            )
