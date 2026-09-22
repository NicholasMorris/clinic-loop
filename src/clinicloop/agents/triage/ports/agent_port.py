"""TriageAgentPort: the triage agent adapter implementing AgentPort."""

import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Literal

from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from langgraph.checkpoint.sqlite import SqliteSaver

from clinicloop.agents.triage.graph.builder import (
    TRIAGE_ALLOWED_MSGPACK_MODULES,
    build_triage_graph,
)
from clinicloop.hitl.decision import HumanDecision
from clinicloop.world.workers import load_agents

from .exceptions import CaseEscalated, DraftNeedsHumanReview, HumanApprovalPending
from .message_source import WorldMessageSource


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
        self._message_source = WorldMessageSource(world)

    def serve(self, case_id: str) -> float:
        """Serve a case with the triage agent.

        Args:
            case_id: The message_id of the support inbox item.

        Returns:
            Service time in minutes.

        Raises:
            RuntimeError: If the case cannot be served (falls back to human queue).
        """
        start = time.perf_counter()

        try:
            # Step b: patient_id lookup
            patient_id = None
            for message in self.world.messages:
                if message.message_id == case_id:
                    patient_id = message.patient_id
                    break

            if patient_id is None:
                raise KeyError(f"Message {case_id} not found in world")

            # Step c: build the graph
            if self.checkpointer_factory is None:
                # Default checkpointer factory
                def default_checkpointer_factory() -> SqliteSaver:
                    """Create a fresh checkpointer for each case."""
                    conn = sqlite3.connect(":memory:", check_same_thread=False)
                    return SqliteSaver(
                        conn,
                        serde=JsonPlusSerializer(allowed_msgpack_modules=TRIAGE_ALLOWED_MSGPACK_MODULES),
                    )

                checkpointer = default_checkpointer_factory()
            else:
                checkpointer = self.checkpointer_factory()

            compiled = build_triage_graph(
                model=self.model,
                tools=self.tools,
                ruleset=self.ruleset,
                message_source=self._message_source,
                outbound_port=self.outbound_port,
                classifier=self.classifier,
                run_key="triage-port",
                checkpointer=checkpointer,
            )

            # Step d: invoke
            cfg = {"configurable": {"thread_id": case_id, "message_id": case_id}}
            compiled.invoke({"case_id": case_id, "patient_id": patient_id}, cfg)

            # Step e: check if paused at human_approval
            next_ = compiled.get_state(cfg).next
            if next_ == ("human_approval",):
                # Auto-approve for simulation purposes
                compiled.update_state(
                    cfg,
                    {
                        "human_decision": HumanDecision(
                            action="approve",
                            decided_by="triage-agent-port",
                            decided_at=datetime.now(timezone.utc),
                        )
                    },
                )
                final_state = compiled.invoke(None, cfg)
            else:
                # Already terminated without pausing
                final_state = compiled.get_state(cfg).values

            # Step f: inspect final state
            escalation_category = final_state.get("escalation_category")
            routing_reason = final_state.get("routing_reason")
            draft = final_state.get("draft")

            # Determine outcome and check for special cases
            if escalation_category not in (None, "none") and draft is None:
                # Escalated
                outcome = "escalated"
                wall_clock_seconds = time.perf_counter() - start
                service_record = ServiceRecord(
                    case_id=case_id,
                    outcome=outcome,
                    wall_clock_seconds=wall_clock_seconds,
                    simulated_minutes=None,
                )
                self.service_log.append(service_record)
                raise CaseEscalated(case_id)
            elif routing_reason in ("language", "rule_block"):
                # Blocked/needs review
                outcome = "human_review"
                wall_clock_seconds = time.perf_counter() - start
                service_record = ServiceRecord(
                    case_id=case_id,
                    outcome=outcome,
                    wall_clock_seconds=wall_clock_seconds,
                    simulated_minutes=None,
                )
                self.service_log.append(service_record)
                raise DraftNeedsHumanReview(case_id, routing_reason)
            else:
                # Guard final ran and allowed, or send already happened via auto-approve
                outcome = "sent"
                agent_config = load_agents()
                simulated_minutes = agent_config.triage.agent_service_minutes
                wall_clock_seconds = time.perf_counter() - start
                service_record = ServiceRecord(
                    case_id=case_id,
                    outcome=outcome,
                    wall_clock_seconds=wall_clock_seconds,
                    simulated_minutes=float(simulated_minutes),
                )
                self.service_log.append(service_record)
                return float(simulated_minutes)

        except (CaseEscalated, DraftNeedsHumanReview, HumanApprovalPending):
            # Re-raise our own exceptions
            raise
        except Exception as exc:
            # Wrap any other exception as RuntimeError for the fallback contract
            wall_clock_seconds = time.perf_counter() - start
            if not isinstance(exc, RuntimeError):
                raise RuntimeError(f"TriageAgentPort.serve() failed: {type(exc).__name__}: {exc}") from exc
            raise
