"""AgentPort protocol for replacing human steps with agent workers."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class AgentPort(Protocol):
    """Protocol for an agent that replaces a simulated human step.

    An AgentPort defines how an agent integrates with the SimClinic engine.
    It replaces one human worker pool (triage, integrity, or consult
    documentation) with an agent that serves cases on the same queue.

    Toggling a port off releases the agent capacity and returns the step
    to its human worker pool, making queue depth and median wait rise.

    A port that raises RuntimeError is caught at the seam: the case falls
    back to the human step and a PortFailure record is written, ensuring
    no case is lost.

    A toggle applies to cases starting after the toggle event and never
    mid-case. Toggle changes take effect at scheduled events, preserving
    run determinism.
    """

    def serve(self, case_id: str) -> float:
        """Serve a case with the agent.

        Called when a case reaches the agent's queue (triage inbox, integrity
        signals queue, or consult note review queue). The agent processes the
        case and returns the service time in minutes.

        If serve() raises RuntimeError (or any exception), the case is
        immediately served by the human worker pool instead, a PortFailure
        record is written, and the run continues.

        Args:
            case_id: Unique case identifier.

        Returns:
            Service time in minutes (must be >= 0).

        Raises:
            RuntimeError: If the agent cannot serve the case; fallback to
                human pool and write PortFailure record.
            Any other exception: Same fallback behavior.
        """
        ...
