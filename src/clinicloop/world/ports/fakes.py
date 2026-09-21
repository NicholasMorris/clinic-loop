"""FakeAgentPort: a deterministic test double shipped in src.

FakeAgentPort replaces real agent adapters (M2-7, M3-3, M5-8) during
development. It ships in src/ (not the test tree) precisely because the
dashboard (M1-7) registers it, and it is later replaced without changing
the seam.

A FakeAgentPort's service time is a configured fraction of the human pool's
mean. With service_time_fraction=0.1, it serves in 1/10 the time. This makes
toggling the agent off visibly worsen queue metrics (depth and wait time rise,
affecting the SLA).
"""

from clinicloop.world.ports.protocol import AgentPort


class FakeAgentPort:
    """A deterministic fake agent that serves in a fraction of human time.

    This port is a test double shipped in src/ for dashboard registration
    and demo purposes. Real agent adapters (M2-7, M3-3, M5-8) replace it
    without changing the seam.

    When enabled, a FakeAgentPort with service_time_fraction=0.1 serves
    cases in 1/10 the time of the human pool's mean. When disabled (toggle
    off), the step reverts to the human pool, making queue depth and median
    wait visibly worse.
    """

    def __init__(self, service_time_fraction: float) -> None:
        """Initialize a fake agent port.

        Args:
            service_time_fraction: Fraction of human pool mean service time
                (e.g., 0.1 means 10% of the human mean).

        Raises:
            ValueError: If service_time_fraction is <= 0 or > 1.
        """
        if service_time_fraction <= 0 or service_time_fraction > 1:
            raise ValueError(
                f"service_time_fraction must be in (0, 1], got {service_time_fraction}"
            )
        self.service_time_fraction = service_time_fraction

    def serve(self, case_id: str) -> float:
        """Serve a case in a fraction of the human mean time.

        For demo purposes, returns a deterministic service time based on the
        service_time_fraction. Real agents (M2-7, M3-3, M5-8) will use this
        same protocol with learned behaviors instead.

        Args:
            case_id: Case identifier.

        Returns:
            Service time in minutes.
        """
        # Stub: minimal implementation for testing protocol
        # Real agents (M2-7, M3-3, M5-8) replace this with actual logic
        return 1.0 * self.service_time_fraction
