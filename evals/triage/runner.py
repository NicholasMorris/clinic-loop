"""Runner for executing triage evaluation cases."""

import hashlib
import json
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, ConfigDict

from evals.triage.golden.loader import GoldenCase


class CaseArtifact(BaseModel):
    """Result of running a single golden case.

    Attributes:
        case_id: The case identifier.
        intent: Expected intent.
        predicted_intent: Predicted intent from the model.
        escalation_category: Expected escalation category.
        predicted_escalation_category: Predicted escalation category.
        guard_allowed: Whether the guard allowed the draft.
        guard_rule_ids: Tuple of rule IDs that matched.
        draft_text_sha256: SHA256 of the draft, or None if escalated.
        reviewer_accepted: Whether the reviewer accepted the draft.
        reviewer_reason: Reason for reviewer rejection, or None if accepted.
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


def run_case(case: GoldenCase, ruleset: Any, elements: Any) -> CaseArtifact:
    """Run a single golden case through the triage graph.

    Args:
        case: The golden case to run.
        ruleset: Guard ruleset.
        elements: Intent elements configuration.

    Returns:
        CaseArtifact with results.
    """
    import sqlite3

    from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
    from langgraph.checkpoint.sqlite import SqliteSaver

    from clinicloop.agents.triage.graph.builder import (
        TRIAGE_ALLOWED_MSGPACK_MODULES,
        build_triage_graph,
    )
    from clinicloop.agents.triage.graph.message_source import InMemoryMessageSource
    from clinicloop.agents.triage.models import CassetteModelPort
    from clinicloop.compliance.outbound.port import OutboundPort
    from evals.triage.reference_reviewer import review

    # Create stub tools that return fixed responses
    class StubTools:
        def __call__(self, action, args):  # type: ignore[no-untyped-def]
            if action == "get_order_status":
                return "Order status: in transit, expected within 3-5 business days."
            elif action == "list_patient_orders":
                return "You have 2 recent orders on file."
            return ""

    # Load cassette
    cassette_path = (
        Path(__file__).resolve().parent.parent.parent
        / "tests"
        / "evals"
        / "triage"
        / "cassettes"
        / "recorded_triage.jsonl"
    )

    # Build the graph
    model = CassetteModelPort(
        "unsloth/Qwen3-30B-A3B-Instruct-2507-GGUF",
        42,
        [cassette_path],
    )

    outbound_port = OutboundPort(lambda text: None, ruleset)
    message_source = InMemoryMessageSource({case.case_id: case.patient_text})

    checkpointer = SqliteSaver(
        sqlite3.connect(":memory:", check_same_thread=False),
        serde=JsonPlusSerializer(allowed_msgpack_modules=TRIAGE_ALLOWED_MSGPACK_MODULES),
    )

    graph = build_triage_graph(
        model=model,
        tools=StubTools(),
        ruleset=ruleset,
        message_source=message_source,
        outbound_port=outbound_port,
        run_key="golden",
        checkpointer=checkpointer,
    )

    # Invoke with the case
    try:
        config = {"configurable": {"thread_id": case.case_id, "message_id": case.case_id}}
        state = graph.invoke({"patient_message_id": case.case_id}, config)

        # Extract results from state
        predicted_intent = state.get("intent")
        predicted_escalation_category = state.get("escalation_category")
        guard_allowed = state.get("guard_allowed")
        guard_rule_ids = tuple(state.get("guard_rule_ids", []))
        draft_text = state.get("draft")

        # Compute draft hash and review
        draft_text_sha256: Optional[str] = None
        reviewer_accepted: Optional[bool] = None
        reviewer_reason: Optional[str] = None

        if draft_text is not None:
            draft_text_sha256 = hashlib.sha256(draft_text.encode()).hexdigest()
            # Run the reviewer
            guard_verdict = state.get("guard_verdict")
            if guard_verdict is not None:
                result = review(
                    draft_text,
                    guard_verdict,
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

    except Exception:
        # If the case fails, return a partial artifact
        return CaseArtifact(
            case_id=case.case_id,
            intent=case.intent,
            escalation_category=case.escalation_category,
        )


def run_all(cases: list[GoldenCase], ruleset: Any, elements: Any) -> list[CaseArtifact]:
    """Run all golden cases.

    Args:
        cases: All golden cases.
        ruleset: Guard ruleset.
        elements: Intent elements configuration.

    Returns:
        List of CaseArtifact objects, one per case in order.
    """
    artifacts = []
    for case in cases:
        artifact = run_case(case, ruleset, elements)
        artifacts.append(artifact)
    return artifacts


def write_artifacts(artifacts: list[CaseArtifact], out_dir: Path) -> None:
    """Write artifacts to disk.

    Args:
        artifacts: List of artifacts.
        out_dir: Output directory.
    """
    out_dir.mkdir(parents=True, exist_ok=True)

    # Write individual artifacts
    for artifact in artifacts:
        case_path = out_dir / f"{artifact.case_id}.json"
        with open(case_path, "w") as f:
            f.write(artifact.model_dump_json(by_alias=False))

    # Write timings (placeholder - real implementation would track elapsed time per case)
    timings_path = out_dir / "timings.json"
    with open(timings_path, "w") as f:
        json.dump({a.case_id: 0.0 for a in artifacts}, f)


def compute_tree_hash(cases: list[GoldenCase], elements: Any) -> str:
    """Compute a stable hash over golden cases and intent elements.

    Args:
        cases: Golden cases.
        elements: Intent elements.

    Returns:
        Hex string SHA256 hash.
    """
    import json

    # Create a stable representation of cases and elements
    cases_dict = [c.model_dump(mode="json") for c in cases]
    elements_dict = elements.model_dump(mode="json")

    combined = {
        "cases": cases_dict,
        "elements": elements_dict,
    }

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

    # Find all .json files except timings.json
    json_files = sorted(
        out_dir.glob("*.json"),
        key=lambda p: p.name,
    )

    for json_file in json_files:
        if json_file.name == "timings.json":
            continue

        with open(json_file) as f:
            data = json.load(f)
        artifacts.append(CaseArtifact(**data))

    return artifacts
