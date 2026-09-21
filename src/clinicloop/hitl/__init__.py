"""Human-in-the-loop kernel for approval gates and checkpointing."""

from clinicloop.hitl.checkpoint import build_checkpointer, checkpoint_root
from clinicloop.hitl.decision import HumanDecision
from clinicloop.hitl.gates import approval_gate, question_loop
from clinicloop.hitl.pending import list_pending
from clinicloop.hitl.reference_graph import ReferenceState, build_reference_graph
from clinicloop.hitl.registry import (
    UnknownAgentGraph,
    get_graph_builder,
    register_graph,
)

# Register the reference graph
register_graph("reference", build_reference_graph)

__all__ = [
    "HumanDecision",
    "build_checkpointer",
    "checkpoint_root",
    "approval_gate",
    "question_loop",
    "list_pending",
    "ReferenceState",
    "build_reference_graph",
    "register_graph",
    "get_graph_builder",
    "UnknownAgentGraph",
]
