"""TriageAgentPort: the triage agent adapter implementing AgentPort."""

from dataclasses import dataclass
from typing import Any, Literal


@dataclass(frozen=True)
class ServiceRecord:
    """Record of a single case service session.

    Attributes:
        case_id: The unique case identifier.
        outcome: The service outcome ('sent', 'escalated', or 'human_review').
        wall_clock_seconds: Wall-clock time elapsed for serve().
        simulated_minutes: Simulated service time in minutes (None for failures).
    """

    case_id: str
    outcome: Literal["sent", "escalated", "human_review"]
    wall_clock_seconds: float
    simulated_minutes: float | None


class TriageAgentPort:
    """Adapter that runs the triage graph as an agent port for support inbox items.

    Attributes:
        service_log: List of ServiceRecord for observability.
    """

    def __init__(
        self,
        *,
        world: Any,
        model: Any,
        tools: Any,
        ruleset: Any,
        outbound_port: Any,
        classifier: Any = None,
        checkpointer_factory: Any = None,
    ) -> None:
        """Initialize the TriageAgentPort.

        Args:
            world: SimClinic world with messages.
            model: ModelPort with complete() method.
            tools: ToolRunner protocol.
            ruleset: Ruleset object.
            outbound_port: OutboundPort implementation.
            classifier: Optional escalation classifier.
            checkpointer_factory: Optional zero-arg callable returning checkpointer.
        """
        self.world = world
        self.model = model
        self.tools = tools
        self.ruleset = ruleset
        self.outbound_port = outbound_port
        self.classifier = classifier
        self.checkpointer_factory = checkpointer_factory
        self.service_log: list[ServiceRecord] = []

    def serve(self, case_id: str) -> float:
        """Serve a case with the triage agent.

        Args:
            case_id: The message_id of the support inbox item.

        Returns:
            Service time in minutes.

        Raises:
            RuntimeError: If the case cannot be served (falls back to human queue).
        """
        raise NotImplementedError("TriageAgentPort.serve() is not yet implemented")
