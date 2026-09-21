"""Agent configuration and registry."""

import tomllib
from pathlib import Path

from pydantic import BaseModel, Field


class AgentConfigParameterMissing(Exception):
    """Raised when a required agent config parameter is missing.

    Attributes:
        agent_name: The name of the agent.
        key: The missing parameter key.
    """

    def __init__(self, agent_name: str, key: str) -> None:
        """Initialize the exception.

        Args:
            agent_name: The name of the agent.
            key: The missing parameter key.
        """
        self.agent_name = agent_name
        self.key = key
        super().__init__(f"Missing parameter '{key}' in agent '{agent_name}'")


class TriageAgentConfig(BaseModel):
    """Configuration for the triage agent.

    Attributes:
        queue: Queue name ("support_inbox").
        agent_resolved_share: Fraction of messages the agent resolves (0-1).
        agent_service_minutes: Service time for agent-resolved messages.
        assumed: Whether the values are assumed.
        assumption_note: Description of what is assumed.
    """

    queue: str = "support_inbox"
    agent_resolved_share: float
    agent_service_minutes: float
    assumed: bool
    assumption_note: str


class ConsultScribeConfig(BaseModel):
    """Configuration for the consult scribe agent.

    Attributes:
        queue: Queue name ("prescriber_review").
        on_extra_minutes: Extra time added to service when agent is ON.
        off_extra_minutes: Extra time added to service when agent is OFF.
        assumed: Whether the values are assumed.
        assumption_note: Description of what is assumed.
    """

    queue: str = "prescriber_review"
    on_extra_minutes: float
    off_extra_minutes: float
    assumed: bool
    assumption_note: str


class IntegrityAgentConfig(BaseModel):
    """Configuration for the integrity agent.

    Attributes:
        queue: Queue name ("intake").
        on_extra_minutes: Extra time added to service when agent is ON.
        off_extra_minutes: Extra time added to service when agent is OFF.
        assumed: Whether the values are assumed.
        assumption_note: Description of what is assumed.
    """

    queue: str = "intake"
    on_extra_minutes: float
    off_extra_minutes: float
    assumed: bool
    assumption_note: str


class AgentRegistry(BaseModel):
    """Registry of all agent configurations.

    Attributes:
        triage: Triage agent configuration.
        consult_scribe: Consult scribe agent configuration.
        integrity: Integrity agent configuration.
    """

    model_config = {"populate_by_name": True}

    triage: TriageAgentConfig
    consult_scribe: ConsultScribeConfig = Field(alias="consult_scribe")
    integrity: IntegrityAgentConfig


def load_agents(config_path: str | Path | None = None) -> AgentRegistry:
    """Load agent configuration from TOML file.

    Args:
        config_path: Path to the agents.toml file.
                   If None, uses the default in src/clinicloop/world/config/agents.toml.

    Returns:
        An AgentRegistry containing all agent configurations.

    Raises:
        AgentConfigParameterMissing: If a required parameter is missing.
        FileNotFoundError: If the config file is not found.
    """
    # Use default path if not provided
    if config_path is None:
        # Get the path to the default agents.toml
        current_file = Path(__file__).resolve()
        config_path = current_file.parent.parent / "config" / "agents.toml"
    else:
        config_path = Path(config_path)

    # Read the TOML file
    with open(config_path, "rb") as f:
        config_data = tomllib.load(f)

    # Parse each agent configuration
    try:
        registry = AgentRegistry(
            triage=config_data.get("triage", {}),
            consult_scribe=config_data.get("consult_scribe", {}),
            integrity=config_data.get("integrity", {}),
        )
        return registry
    except Exception as e:
        raise AgentConfigParameterMissing("agents", "parse_error") from e
