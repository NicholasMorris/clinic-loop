"""Streamlit dashboard app for SimClinic metrics."""

from pathlib import Path

import pandas as pd
import streamlit as st

from clinicloop.dashboard.runner import (
    SEED,
    build_registry,
    run_with_toggles,
    snapshot_path,
)
from clinicloop.world.metrics import read_run_snapshot


def main() -> None:
    """Render the SimClinic metrics dashboard."""
    st.set_page_config(page_title="SimClinic Dashboard", layout="wide")
    st.title("SimClinic Dashboard")

    # Initialize session state for toggle tracking
    if "recomputed" not in st.session_state:
        st.session_state["recomputed"] = False

    # Define toggle configuration: (scope, label)
    toggle_config = [
        ("triage", "Triage agent"),
        ("integrity", "Integrity signals agent"),
        ("consult_documentation", "Consult documentation agent"),
    ]

    # Verify all scopes are in the registry
    registry = build_registry()
    for scope, _label in toggle_config:
        assert scope in registry.toggleable_scopes(), f"Scope {scope} not in registry"

    # Create toggle widgets with on_change callback
    st.subheader("Agent toggles")

    col1, col2, col3 = st.columns(3)

    with col1:
        toggle_triage = st.toggle(
            "Triage agent",
            value=True,
            key="toggle_triage",
            on_change=lambda: st.session_state.update({"recomputed": True}),
        )

    with col2:
        toggle_integrity = st.toggle(
            "Integrity signals agent",
            value=True,
            key="toggle_integrity",
            on_change=lambda: st.session_state.update({"recomputed": True}),
        )

    with col3:
        toggle_consult_documentation = st.toggle(
            "Consult documentation agent",
            value=True,
            key="toggle_consult_documentation",
            on_change=lambda: st.session_state.update({"recomputed": True}),
        )

    # Data path selection based on session state
    if st.session_state["recomputed"]:
        # Path B: Re-run engine with current toggle values
        toggles = {
            "triage": toggle_triage,
            "integrity": toggle_integrity,
            "consult_documentation": toggle_consult_documentation,
        }
        snapshot, max_depths = run_with_toggles(toggles)
    else:
        # Path A: Read snapshot file on first paint
        snap_path = snapshot_path()
        if not snap_path.exists():
            st.info(
                "Snapshot file not found. Run `make sim-snapshot` to generate it.\n\n"
                "```\nmake sim-snapshot\n```"
            )
            st.stop()

        snapshot = read_run_snapshot(snap_path)
        # First paint: max_depths come from file if available, or None
        max_depths = {q: None for q in ["intake", "prescriber_review", "pharmacy_fulfilment", "support_inbox"]}

    # Render metric panels
    st.subheader("Metrics")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Throughput",
            f"{snapshot.throughput.orders_completed} orders",
        )

    with col2:
        # Find the queue with the maximum median wait
        max_wait = None
        slowest_queue = None
        for queue, wait in snapshot.median_wait_minutes.items():
            if wait is not None and (max_wait is None or wait > max_wait):
                max_wait = wait
                slowest_queue = queue

        if max_wait is not None:
            value = f"{max_wait:.1f} min"
            help_text = f"Slowest queue: {slowest_queue}"
        else:
            value = "n/a"
            help_text = None

        st.metric("Median wait", value, help=help_text)

    with col3:
        total_breaches = sum(b.count for b in snapshot.sla_breaches.values())
        st.metric("SLA breaches", total_breaches)

    with col4:
        if snapshot.cost_per_order is not None:
            value = f"${snapshot.cost_per_order:.2f}"
        else:
            value = "n/a"
        st.metric("Cost per order", value)

    # Queue metrics table
    st.subheader("Queues")

    queue_data = []
    for queue_name in ["intake", "prescriber_review", "pharmacy_fulfilment", "support_inbox"]:
        median_wait = snapshot.median_wait_minutes.get(queue_name)
        max_depth = max_depths.get(queue_name)
        queue_data.append(
            {
                "queue": queue_name,
                "median_wait_minutes": median_wait,
                "max_queue_depth": max_depth,
            }
        )

    queue_df = pd.DataFrame(queue_data)
    st.dataframe(queue_df, use_container_width=True, hide_index=True)

    # SLA breach detail table
    st.subheader("SLA breaches")

    breach_data = []
    for rule_id, breach in snapshot.sla_breaches.items():
        breach_data.append(
            {
                "rule_id": breach.rule_id,
                "inventory_id": breach.inventory_id,
                "count": breach.count,
            }
        )

    if breach_data:
        breach_df = pd.DataFrame(breach_data)
        st.dataframe(breach_df, use_container_width=True, hide_index=True)
    else:
        st.info("No SLA breaches in this run.")

    # Information about FakeAgentPort
    st.caption(
        "The three agents shown above are currently served by the shipped FakeAgentPort "
        "(10% of human service time) until the real adapters land (M2-7, M3-3, M5-8)."
    )


if __name__ == "__main__":
    main()
