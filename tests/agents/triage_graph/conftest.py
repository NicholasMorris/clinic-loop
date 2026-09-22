"""Fixtures for triage graph tests."""

import json
from pathlib import Path

import pytest

from clinicloop.agents.triage.graph.message_source import InMemoryMessageSource
from clinicloop.agents.triage.models import FakeModelPort
from clinicloop.agents.triage.tools import ToolRunner


@pytest.fixture
def injection_pairs() -> list[dict]:
    """Load injection pairs from fixture file.

    Returns:
        List of pair dicts with clean/injected threads and expected intents/tools.
    """
    fixture_path = Path(__file__).parent / "fixtures" / "injection_pairs.jsonl"
    pairs = []
    if fixture_path.exists():
        with open(fixture_path) as f:
            for line in f:
                pairs.append(json.loads(line))
    return pairs


@pytest.fixture
def message_source() -> InMemoryMessageSource:
    """Create an InMemoryMessageSource with test messages.

    Returns:
        An InMemoryMessageSource populated with test messages.
    """
    messages = {
        "msg-001": "I need to check my order status",
        "msg-002": "Could you help me cancel my order?",
        "msg-003": "When will my delivery arrive?",
    }
    return InMemoryMessageSource(messages)


@pytest.fixture
def fake_model() -> FakeModelPort:
    """Create a FakeModelPort for testing.

    Returns:
        A FakeModelPort with scripted responses.
    """
    return FakeModelPort(responses=['{"intent": "order_status"}'])


@pytest.fixture
def fake_tools() -> ToolRunner:
    """Create a mock ToolRunner.

    Returns:
        A ToolRunner that returns fake results.
    """

    class MockToolRunner:
        def run(self, tool_name: str, patient_id: str, order_id: str | None) -> str:
            if tool_name == "get_order_status":
                return f"Order {order_id} is in transit"
            elif tool_name == "list_patient_orders":
                return f"Patient {patient_id} has 2 orders"
            return ""

    return MockToolRunner()  # type: ignore[return-value]
