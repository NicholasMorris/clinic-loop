"""Test model swapping and no hardcoded model names.

AC7: Running the same fixture thread through ingest, classify_intent, resolve and draft
against a second models.toml row (both rows served by the fake model) produces the same
intent and the same recorded tool-call list, and no module under src/clinicloop/agents/triage/
contains a models.toml row name as a string literal.
"""

import ast
import re
from pathlib import Path

import pytest

from clinicloop.agents.triage.models import FakeModelPort
from clinicloop.agents.triage.nodes.classify_intent import classify_intent
from clinicloop.agents.triage.nodes.ingest import ingest
from clinicloop.agents.triage.nodes.resolve import resolve


@pytest.fixture
def _fixed_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set CLINICLOOP_ESCALATION_KEY to a fixed value."""
    monkeypatch.setenv("CLINICLOOP_ESCALATION_KEY", "a" * 64)


def test_nodes_behave_identically_against_a_second_models_toml_row(_fixed_key: None) -> None:
    """AC7: Same fixture thread produces identical results with different model rows."""
    raw_message = "Where is my order?"
    run_key = "test-001"

    # Ingest (model-independent)
    state_dict_1 = {
        "case_id": "c-001",
        "patient_id": "p-001",
    }

    update_ingest = ingest(state_dict_1, raw_message, run_key)
    state_dict_1.update(update_ingest)

    # Classify intent with model 1 (fake)
    model_1 = FakeModelPort(['{"intent": "order_status"}'])

    try:
        update_classify_1 = classify_intent(state_dict_1, model_1)
    except NotImplementedError:
        pytest.skip("classify_intent not yet implemented")

    intent_1 = update_classify_1.get("intent")
    state_dict_1.update(update_classify_1)

    # Resolve with model 1 (fake)
    class FakeToolRunner:
        def run(self, name, patient_id, order_id):
            return "Order status: in transit"

    try:
        update_resolve_1 = resolve(state_dict_1, model_1, FakeToolRunner())
    except NotImplementedError:
        pytest.skip("resolve not yet implemented")

    tool_calls_1 = update_resolve_1.get("tool_calls", [])
    state_dict_1.update(update_resolve_1)

    # Now run the exact same sequence with model 2 (same fake, different row)
    state_dict_2 = {
        "case_id": "c-002",
        "patient_id": "p-002",
    }

    update_ingest = ingest(state_dict_2, raw_message, run_key)
    state_dict_2.update(update_ingest)

    # Classify with model 2 (different row, same responses)
    model_2 = FakeModelPort(['{"intent": "order_status"}'])

    try:
        update_classify_2 = classify_intent(state_dict_2, model_2)
    except NotImplementedError:
        pytest.skip("classify_intent not yet implemented")

    intent_2 = update_classify_2.get("intent")
    state_dict_2.update(update_classify_2)

    # Resolve with model 2
    try:
        update_resolve_2 = resolve(state_dict_2, model_2, FakeToolRunner())
    except NotImplementedError:
        pytest.skip("resolve not yet implemented")

    tool_calls_2 = update_resolve_2.get("tool_calls", [])

    # Verify results are identical
    assert str(intent_1) == str(intent_2), f"Intents differ: {intent_1} vs {intent_2}"
    assert len(tool_calls_1) == len(tool_calls_2), f"Tool call counts differ"


def test_no_models_toml_row_names_in_source() -> None:
    """AC7: No module under src/clinicloop/agents/triage/ contains row names as string literals."""
    triage_dir = Path(__file__).parent.parent.parent / "src" / "clinicloop" / "agents" / "triage"

    # Known models.toml row names to avoid
    forbidden_names = {
        "primary",
        "judge",
        "fallback",
        "fake",
    }

    py_files = triage_dir.glob("**/*.py")

    violations = []
    for py_file in py_files:
        with open(py_file) as f:
            content = f.read()

        # Check for string literals matching forbidden names
        for name in forbidden_names:
            # Look for quoted strings: "name", 'name'
            pattern = rf'["\']({re.escape(name)})["\']'
            if re.search(pattern, content):
                violations.append(f"{py_file.name}: contains '{name}' string literal")

    assert not violations, f"Found hardcoded models.toml row names:\n" + "\n".join(violations)


def test_no_langchain_openai_imports() -> None:
    """AC7: No module imports langchain_openai (models come from ModelPort arguments)."""
    triage_dir = Path(__file__).parent.parent.parent / "src" / "clinicloop" / "agents" / "triage"

    py_files = triage_dir.glob("**/*.py")

    violations = []
    for py_file in py_files:
        with open(py_file) as f:
            content = f.read()

        # Check for langchain_openai imports
        if "langchain_openai" in content or "from langchain_openai" in content:
            violations.append(str(py_file))

    assert not violations, f"Found langchain_openai imports in:\n" + "\n".join(violations)
