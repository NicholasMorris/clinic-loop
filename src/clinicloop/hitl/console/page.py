"""Streamlit page for the review console."""

import streamlit as st

from clinicloop.hitl.console.backend import apply_decision, list_pending
from clinicloop.hitl.console.errors import DecisionAlreadyRecorded, UnknownDecisionKind


def main() -> None:
    """Main Streamlit app for the review console."""
    st.set_page_config(page_title="Review Console", layout="wide")
    st.title("Review Console")

    flash = st.session_state.pop("flash", None)
    if flash:
        st.success(flash)

    # Fetch pending items
    listing = list_pending()

    # Display any errors
    for error in listing.errors:
        st.error(f"Error reading agent '{error.agent}': {error.message}")

    if not listing.items:
        st.info("No pending items awaiting review.")
        return

    st.subheader("Pending Items")
    st.dataframe(
        [
            {
                "Agent": item.agent,
                "Case ID": item.case_id,
                "Node": item.node,
                "Interrupted At": item.interrupted_at,
            }
            for item in listing.items
        ],
        width="stretch",
        hide_index=True,
    )

    labels = [f"{item.agent}/{item.case_id}" for item in listing.items]
    choice = st.selectbox("Item to review", labels, key="selected_item")
    item = listing.items[labels.index(choice)]

    # Display item details
    st.subheader(f"Review Item: {item.agent}/{item.case_id}")

    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Agent:** {item.agent}")
        st.write(f"**Case ID:** {item.case_id}")
        st.write(f"**Interrupted Node:** {item.node}")
        st.write(f"**Interrupted At:** {item.interrupted_at}")

    with col2:
        pass

    st.subheader("Payload")
    st.json(item.payload)

    # Decision form
    st.subheader("Apply Decision")

    reviewer = st.text_input("Reviewer ID", key="reviewer_id")
    decision_kind = st.radio(
        "Decision",
        ["approve", "edit", "reject"],
        key="decision_kind",
    )

    edited_text = None
    reason = None

    if decision_kind == "edit":
        edited_text = st.text_area(
            "Edited Text",
            value=str(item.payload.get("case_id", "")),
            key="edited_text",
        )

    if decision_kind == "reject":
        reason = st.text_area("Reason", key="reason")

    if st.button("Apply Decision"):
        if not reviewer:
            st.error("Reviewer ID is required.")
            return

        try:
            apply_decision(
                agent=item.agent,
                case_id=item.case_id,
                kind=decision_kind,
                reviewer=reviewer,
                edited_text=edited_text,
                reason=reason,
            )
            st.session_state["flash"] = f"Decision recorded for {item.agent}/{item.case_id}."
            st.rerun()
        except DecisionAlreadyRecorded:
            st.error("A decision has already been recorded for this item.")
        except UnknownDecisionKind:
            st.error(f"Unknown decision kind: {decision_kind}")
        except Exception as e:
            st.error(f"Error applying decision: {e}")


if __name__ == "__main__":
    main()
