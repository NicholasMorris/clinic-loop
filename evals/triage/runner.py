"""Runner for executing triage evaluation cases."""

import hashlib
import json
import time
from dataclasses import asdict
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


def run_case(case: GoldenCase, ruleset, elements) -> CaseArtifact:
    """Run a single golden case through the triage graph.

    Args:
        case: The golden case to run.
        ruleset: Guard ruleset.
        elements: Intent elements configuration.

    Returns:
        CaseArtifact with results.
    """
    raise NotImplementedError("run_case not yet implemented")


def run_all(cases: list[GoldenCase], ruleset, elements) -> list[CaseArtifact]:
    """Run all golden cases.

    Args:
        cases: All golden cases.
        ruleset: Guard ruleset.
        elements: Intent elements configuration.

    Returns:
        List of CaseArtifact objects, one per case in order.
    """
    raise NotImplementedError("run_all not yet implemented")


def write_artifacts(artifacts: list[CaseArtifact], out_dir: Path) -> None:
    """Write artifacts to disk.

    Args:
        artifacts: List of artifacts.
        out_dir: Output directory.
    """
    raise NotImplementedError("write_artifacts not yet implemented")


def compute_tree_hash(cases: list[GoldenCase], elements) -> str:
    """Compute a stable hash over golden cases and intent elements.

    Args:
        cases: Golden cases.
        elements: Intent elements.

    Returns:
        Hex string SHA256 hash.
    """
    raise NotImplementedError("compute_tree_hash not yet implemented")


def load_artifacts(out_dir: Path) -> list[CaseArtifact]:
    """Load artifacts from disk.

    Args:
        out_dir: Directory containing case_id.json files.

    Returns:
        List of CaseArtifact objects loaded from JSON files.
    """
    raise NotImplementedError("load_artifacts not yet implemented")
