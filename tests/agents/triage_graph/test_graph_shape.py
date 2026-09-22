"""Test the shape of the compiled triage graph.

AC1: The compiled graph's node set equals EXPECTED_NODES and all happy-path edges are present.
"""


from clinicloop.agents.triage.graph.builder import build_triage_graph
from clinicloop.agents.triage.graph.nodes import EXPECTED_NODES
from clinicloop.agents.triage.models import FakeModelPort
from clinicloop.compliance.outbound.port import OutboundPort
from clinicloop.compliance.rulesets import load_ruleset


def test_node_set_equals_expected_nodes_and_happy_path_edges_present(
    fake_model: FakeModelPort,
    message_source,
    fake_tools,
) -> None:
    """Verify graph has exactly EXPECTED_NODES and all happy-path edges.

    Happy-path edges from docs/agents/triage.md:
    1. ingest -> classify_intent
    2. classify_intent -> escalation_check
    3. escalation_check -> resolve (when no escalation)
    4. resolve -> draft
    5. draft -> regulatory_guard
    6. regulatory_guard -> human_approval
    7. human_approval -> guard_final (after decision)
    8. guard_final -> send
    9. send -> END
    Plus: escalation_check -> escalate (when escalated)
    """
    # Create dummy transport
    calls: list[str] = []
    transport = calls.append

    ruleset = load_ruleset("au")

    # Build graph
    compiled = build_triage_graph(
        model=fake_model,
        tools=fake_tools,  # type: ignore[arg-type]
        ruleset=ruleset,
        message_source=message_source,
        outbound_port=OutboundPort(transport, ruleset),
        run_key="test",
    )

    # Get graph structure
    graph = compiled.get_graph()
    node_names = set(graph.nodes.keys()) - {"__start__", "__end__"}

    # AC1a: Node set should equal EXPECTED_NODES
    assert node_names == set(EXPECTED_NODES), f"Expected {set(EXPECTED_NODES)}, got {node_names}"

    # AC1b: Check happy-path edges are present
    edges = {(edge.source, edge.target): edge for edge in graph.edges}

    happy_path_edges = [
        ("ingest", "classify_intent"),
        ("classify_intent", "escalation_check"),
        ("escalation_check", "resolve"),  # conditional: 'continue'
        ("resolve", "draft"),  # conditional: 'ok'
        ("draft", "regulatory_guard"),  # conditional: 'ok'
        ("regulatory_guard", "human_approval"),  # conditional: 'ok'
        ("human_approval", "guard_final"),  # conditional: approve/edit
        ("guard_final", "send"),  # conditional: 'ok'
        ("escalation_check", "escalate"),  # conditional: 'escalate'
    ]

    for source, target in happy_path_edges:
        assert (
            source,
            target,
        ) in edges, f"Missing edge {source} -> {target}"
