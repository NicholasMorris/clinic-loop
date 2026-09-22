"""Test that a genuine failure resuming after auto-approval raises HumanApprovalPending.

Per docs/agents/triage-agent-port.md, HumanApprovalPending should be raised
"if update_state() or the post-approval invoke() raises an exception during the
auto-approval resume." Nothing in the checkpointer/graph naturally fails this
way, so this test injects a real failure via a checkpointer whose `put()`
starts raising partway through -- specifically, the first `put()` that occurs
after the case has already paused at human_approval once (determined
empirically per-case, since the exact number of internal checkpoint writes is
an implementation detail of the graph, not a contract this test should hardcode).
"""

import sqlite3

from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import Checkpoint, CheckpointMetadata
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from langgraph.checkpoint.sqlite import SqliteSaver

from clinicloop.agents.triage.graph.builder import (
    TRIAGE_ALLOWED_MSGPACK_MODULES,
)
from clinicloop.agents.triage.models import FakeModelPort
from clinicloop.agents.triage.ports.agent_port import TriageAgentPort
from clinicloop.agents.triage.ports.exceptions import HumanApprovalPending
from clinicloop.compliance.outbound.port import OutboundPort
from clinicloop.compliance.rulesets import load_ruleset


class InstantToolRunner:
    """Returns a fixed summary immediately."""

    def run(self, name: str, patient_id: str, order_id: str | None) -> str:
        """Return a fixed summary."""
        return f"Order {order_id} is in transit"


class FakeMessage:
    """A minimal stand-in for a world message."""

    def __init__(self, message_id: str, patient_id: str, body: str) -> None:
        """Store the message fields."""
        self.message_id = message_id
        self.patient_id = patient_id
        self.body = body


class FakeWorld:
    """A minimal stand-in for a world exposing only .messages."""

    def __init__(self, messages: list[FakeMessage]) -> None:
        """Store the messages list."""
        self.messages = messages


class CountingSaver(SqliteSaver):
    """A SqliteSaver that counts every put() call."""

    def __init__(self, conn: sqlite3.Connection, serde: JsonPlusSerializer) -> None:
        """Wrap a real SqliteSaver with a call counter."""
        super().__init__(conn, serde=serde)
        self.put_calls = 0

    def put(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: dict[str, str | int | float],
    ) -> RunnableConfig:
        """Count and delegate."""
        self.put_calls += 1
        return super().put(config, checkpoint, metadata, new_versions)


class PoisonedSaver(SqliteSaver):
    """A SqliteSaver whose put() raises from the given call number onward."""

    def __init__(
        self, conn: sqlite3.Connection, serde: JsonPlusSerializer, fail_from_call: int
    ) -> None:
        """Wrap a real SqliteSaver with a call counter and a failure threshold."""
        super().__init__(conn, serde=serde)
        self._put_calls = 0
        self._fail_from_call = fail_from_call

    def put(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: dict[str, str | int | float],
    ) -> RunnableConfig:
        """Count, then raise once the threshold is reached."""
        self._put_calls += 1
        if self._put_calls >= self._fail_from_call:
            raise ValueError("simulated guard_final failure on resume")
        return super().put(config, checkpoint, metadata, new_versions)


def _make_port(checkpointer_factory: object) -> tuple[TriageAgentPort, list[str]]:
    world = FakeWorld([FakeMessage("case-resume-fail", "patient-1", "What is my order status?")])
    model = FakeModelPort(['{"intent": "general_question"}', "Your order is on the way."])
    ruleset = load_ruleset("au")
    sent_texts: list[str] = []
    outbound = OutboundPort(sent_texts.append, ruleset)
    port = TriageAgentPort(
        world=world,
        model=model,
        tools=InstantToolRunner(),
        ruleset=ruleset,
        outbound_port=outbound,
        classifier=None,
        checkpointer_factory=checkpointer_factory,
    )
    return port, sent_texts


def test_resume_failure_raises_human_approval_pending() -> None:
    """A ValueError raised while resuming after auto-approval surfaces as HumanApprovalPending."""
    # First, learn how many put() calls a normal happy-path run makes before
    # completion (this includes the pre-pause writes and the resume writes).
    counting_holder: dict[str, CountingSaver] = {}

    def counting_factory() -> CountingSaver:
        conn = sqlite3.connect(":memory:", check_same_thread=False)
        saver = CountingSaver(
            conn, serde=JsonPlusSerializer(allowed_msgpack_modules=TRIAGE_ALLOWED_MSGPACK_MODULES)
        )
        counting_holder["saver"] = saver
        return saver

    baseline_port, _ = _make_port(counting_factory)
    baseline_port.serve("case-resume-fail")
    total_calls = counting_holder["saver"].put_calls
    assert total_calls > 1, "Expected multiple checkpoint writes across pause + resume"

    # Poison 3 calls before the happy-path total. Empirically (see module
    # docstring), the last 3 put() calls on this graph correspond to the
    # guard_final node committing its send, and two bookkeeping writes after
    # it -- failing any of those lets the send through first. Failing the
    # 4th-from-last call interrupts the resume before guard_final's own
    # commit, so the send never happens.
    def poisoned_factory() -> PoisonedSaver:
        conn = sqlite3.connect(":memory:", check_same_thread=False)
        return PoisonedSaver(
            conn,
            serde=JsonPlusSerializer(allowed_msgpack_modules=TRIAGE_ALLOWED_MSGPACK_MODULES),
            fail_from_call=total_calls - 3,
        )

    poisoned_port, sent_texts = _make_port(poisoned_factory)
    try:
        poisoned_port.serve("case-resume-fail")
        raise AssertionError("Expected HumanApprovalPending to be raised")
    except HumanApprovalPending as exc:
        assert exc.case_id == "case-resume-fail"

    assert sent_texts == [], "A failed resume must never send a draft"
    assert poisoned_port.service_log[-1].outcome == "human_review"
