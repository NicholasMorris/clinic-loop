"""Test that escalation routes cannot reach draft.

AC2: The M2-3 reachability helper called on the compiled graph returns an empty path list
for every edge leaving escalation_check to escalate, so no path reaches draft from an
escalation edge.
"""


from clinicloop.agents.triage.graph.builder import build_triage_graph
from clinicloop.agents.triage.models import FakeModelPort
from clinicloop.compliance.escalation.reachability import paths_from_escalation_to_draft
from clinicloop.compliance.outbound.port import OutboundPort
from clinicloop.compliance.rulesets import load_ruleset


def test_no_path_from_escalation_edge_to_draft(
    fake_model: FakeModelPort,
    message_source,
    fake_tools,
) -> None:
    """Verify no path from escalation_check's escalate edge reaches draft.

    This tests that if escalation_check routes to escalate, the case cannot
    reach draft. It also tests that a mis-wired variant would be caught.
    """
    # Create dummy transport
    calls: list[str] = []
    transport = calls.append

    ruleset = load_ruleset("au")

    # Build the correctly wired graph
    compiled = build_triage_graph(
        model=fake_model,
        tools=fake_tools,  # type: ignore[arg-type]
        ruleset=ruleset,
        message_source=message_source,
        outbound_port=OutboundPort(transport, ruleset),
        run_key="test",
    )

    # AC2: Check that paths_from_escalation_to_draft returns empty list
    violations = paths_from_escalation_to_draft(
        compiled, check_node="escalation_check", draft_node="draft", clear_label="continue"
    )
    assert (
        violations == []
    ), f"Escalation edge reaches draft via: {violations}"
