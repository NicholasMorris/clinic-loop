"""Runner for executing triage evaluation cases."""

import hashlib
import json
import sqlite3
import time
from pathlib import Path
from typing import Any, Optional

from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from langgraph.checkpoint.sqlite import SqliteSaver
from pydantic import BaseModel, ConfigDict

from clinicloop.agents.triage.graph.builder import (
    TRIAGE_ALLOWED_MSGPACK_MODULES,
    build_triage_graph,
)
from clinicloop.agents.triage.graph.message_source import InMemoryMessageSource
from clinicloop.agents.triage.models import CassetteModelPort
from clinicloop.compliance.outbound.port import OutboundPort
from evals.triage.golden.loader import GoldenCase
from evals.triage.reference_reviewer import review

CASSETTE_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "tests"
    / "evals"
    / "triage"
    / "cassettes"
    / "recorded_triage.jsonl"
)
MODEL_ID = "unsloth/Qwen3-30B-A3B-Instruct-2507-GGUF"
MODEL_SEED = 42


class StubTools:
    """Deterministic tool stub matching the real ToolRunner protocol.

    Fixed responses matching exactly what the cassette was recorded against
    (see docs/evaluation/triage.md): the resolve prompt itself does not depend
    on the tool result, but keeping it byte-identical to the recording keeps
    the whole eval reproducible if a future node ever does depend on it.
    """

    def run(self, name: str, patient_id: str, order_id: str | None) -> str:
        """Return a fixed factual summary for a tool name."""
        if name == "get_order_status":
            return "Order status: in transit, expected within 3-5 business days."
        if name == "list_patient_orders":
            return "You have 2 recent orders on file."
        return ""


class CaseArtifact(BaseModel):
    """Result of running a single golden case.

    Attributes:
        case_id: The case identifier.
        intent: Expected intent.
        predicted_intent: Predicted intent from the model.
        escalation_category: Expected escalation category.
        predicted_escalation_category: Predicted escalation category.
        guard_allowed: Whether the guard allowed the draft, or None if no
            draft was ever produced (an escalating or language-blocked case).
        guard_rule_ids: Tuple of rule IDs on the last guard verdict.
        draft_text_sha256: SHA256 of the draft, or None if no draft.
        reviewer_accepted: Whether the reviewer accepted the draft.
        reviewer_reason: Reason for reviewer rejection, or None if accepted
            or not reviewed.
        review_method: Always 'rule-based reference reviewer'.
    """

    case_id: str
    intent: str
    predicted_intent: Optional[str] = None
    escalation_category: str
    predicted_escalation_category: Optional[str] = None
    guard_allowed: Optional[bool] = None
    guard_rule_ids: tuple[str, ...] = ()
    draft_text_sha256: Optional[str] = None
    reviewer_accepted: Optional[bool] = None
    reviewer_reason: Optional[str] = None
    review_method: str = "rule-based reference reviewer"

    model_config = ConfigDict(frozen=True)


def _build_graph(case: GoldenCase, ruleset: Any) -> Any:
    """Build a fresh, isolated triage graph for one golden case."""
    model = CassetteModelPort(MODEL_ID, MODEL_SEED, [CASSETTE_PATH])
    outbound_port = OutboundPort(lambda text: None, ruleset)
    message_source = InMemoryMessageSource({case.case_id: case.patient_text})
    checkpointer = SqliteSaver(
        sqlite3.connect(":memory:", check_same_thread=False),
        serde=JsonPlusSerializer(allowed_msgpack_modules=TRIAGE_ALLOWED_MSGPACK_MODULES),
    )
    return build_triage_graph(
        model=model,
        tools=StubTools(),
        ruleset=ruleset,
        message_source=message_source,
        outbound_port=outbound_port,
        run_key="golden",
        checkpointer=checkpointer,
    )


def run_case(case: GoldenCase, ruleset: Any, elements: Any) -> CaseArtifact:
    """Run a single golden case through the real triage graph.

    A CassetteMiss or any other exception from the graph itself propagates
    as a real failure; it is never caught and turned into a placeholder
    artifact, since that would silently hide a broken run behind numbers
    that look measured but are not.

    Args:
        case: The golden case to run.
        ruleset: Guard ruleset.
        elements: Intent elements configuration.

    Returns:
        CaseArtifact with results.
    """
    graph = _build_graph(case, ruleset)
    config = {"configurable": {"thread_id": case.case_id, "message_id": case.case_id}}
    state = graph.invoke({"case_id": case.case_id, "patient_id": f"P-{case.case_id}"}, config)

    predicted_intent_obj = state.get("intent")
    predicted_intent = predicted_intent_obj.value if predicted_intent_obj is not None else None
    predicted_escalation_category = state.get("escalation_category")
    draft_text = state.get("draft")

    guard_verdicts = state.get("guard_verdicts") or []
    final_verdict = guard_verdicts[-1] if guard_verdicts else None
    guard_allowed = final_verdict.allowed if final_verdict is not None else None
    guard_rule_ids = tuple(final_verdict.rule_ids) if final_verdict is not None else ()

    draft_text_sha256: Optional[str] = None
    reviewer_accepted: Optional[bool] = None
    reviewer_reason: Optional[str] = None

    if draft_text is not None:
        draft_text_sha256 = hashlib.sha256(draft_text.encode()).hexdigest()
        if final_verdict is not None:
            result = review(
                draft_text,
                final_verdict,
                predicted_intent or "",
                elements=elements,
                ruleset=ruleset,
            )
            reviewer_accepted = result.accepted
            reviewer_reason = result.reason

    return CaseArtifact(
        case_id=case.case_id,
        intent=case.intent,
        predicted_intent=predicted_intent,
        escalation_category=case.escalation_category,
        predicted_escalation_category=predicted_escalation_category,
        guard_allowed=guard_allowed,
        guard_rule_ids=guard_rule_ids,
        draft_text_sha256=draft_text_sha256,
        reviewer_accepted=reviewer_accepted,
        reviewer_reason=reviewer_reason,
        review_method="rule-based reference reviewer",
    )


def run_all(
    cases: list[GoldenCase], ruleset: Any, elements: Any
) -> tuple[list[CaseArtifact], dict[str, float]]:
    """Run all golden cases in order, timing each one.

    Args:
        cases: All golden cases.
        ruleset: Guard ruleset.
        elements: Intent elements configuration.

    Returns:
        (artifacts, timings) -- one CaseArtifact per case in case_id order,
        and a dict of case_id -> real elapsed wall-clock seconds.
    """
    artifacts = []
    timings: dict[str, float] = {}
    for case in cases:
        started = time.perf_counter()
        artifact = run_case(case, ruleset, elements)
        timings[case.case_id] = time.perf_counter() - started
        artifacts.append(artifact)
    return artifacts, timings


def write_artifacts(
    artifacts: list[CaseArtifact], out_dir: Path, timings: dict[str, float] | None = None
) -> None:
    """Write artifacts and their timings to disk.

    Args:
        artifacts: List of artifacts.
        out_dir: Output directory.
        timings: Optional case_id -> elapsed_seconds map from run_all. When
            omitted, every case's timing is recorded as 0.0 rather than a
            fabricated non-zero number.
    """
    out_dir.mkdir(parents=True, exist_ok=True)

    for artifact in artifacts:
        case_path = out_dir / f"{artifact.case_id}.json"
        with open(case_path, "w") as f:
            f.write(artifact.model_dump_json(by_alias=False))

    timings = timings or {}
    timings_path = out_dir / "timings.json"
    with open(timings_path, "w") as f:
        json.dump({a.case_id: timings.get(a.case_id, 0.0) for a in artifacts}, f)


def compute_tree_hash(cases: list[GoldenCase], elements: Any) -> str:
    """Compute a stable hash over golden cases and intent elements.

    Args:
        cases: Golden cases.
        elements: Intent elements.

    Returns:
        Hex string SHA256 hash.
    """
    cases_dict = [c.model_dump(mode="json") for c in cases]
    elements_dict = elements.model_dump(mode="json")
    combined = {"cases": cases_dict, "elements": elements_dict}
    combined_json = json.dumps(combined, sort_keys=True)
    return hashlib.sha256(combined_json.encode()).hexdigest()


def load_artifacts(out_dir: Path) -> list[CaseArtifact]:
    """Load artifacts from disk.

    Args:
        out_dir: Directory containing case_id.json files.

    Returns:
        List of CaseArtifact objects loaded from JSON files.
    """
    artifacts = []
    json_files = sorted(out_dir.glob("*.json"), key=lambda p: p.name)

    for json_file in json_files:
        if json_file.name == "timings.json":
            continue
        with open(json_file) as f:
            data = json.load(f)
        artifacts.append(CaseArtifact(**data))

    return artifacts
