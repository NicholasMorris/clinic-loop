"""Tool runner protocol and implementations for triage resolve node."""

from typing import Any, Protocol


class ToolError(Exception):
    """Raised when a tool call fails."""

    pass


# Tool names available for resolution
TOOL_NAMES = ("get_order_status", "list_patient_orders")


class ToolRunner(Protocol):
    """Protocol for running tools in the resolve node."""

    def run(self, name: str, patient_id: str, order_id: str | None) -> str:
        """Run a named tool and return a short factual summary.

        Args:
            name: Tool name from TOOL_NAMES.
            patient_id: Patient ID (bound from state, not model output).
            order_id: Order ID (bound from state, not model output).

        Returns:
            Short factual summary of the result (status and dates only, never names/IDs).

        Raises:
            ToolError: If the tool call fails (non-200 status).
        """
        ...


class ApiToolRunner:
    """Tool runner that calls a mock API (httpx.Client or fastapi.TestClient)."""

    def __init__(self, client: Any) -> None:
        """Initialize with an API client.

        Args:
            client: Object with .get(path) -> response with .status_code and .json().
        """
        self.client = client

    def run(self, name: str, patient_id: str, order_id: str | None) -> str:
        """Run a tool by calling the API.

        Args:
            name: Tool name.
            patient_id: Patient ID.
            order_id: Order ID.

        Returns:
            Short factual summary.

        Raises:
            ToolError: If the API call fails.
            NotImplementedError: Until implemented.
        """
        raise NotImplementedError("ApiToolRunner.run not yet implemented")
