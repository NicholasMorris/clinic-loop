"""Registry for LangGraph agent builders."""

from typing import Any, Callable


class UnknownAgentGraph(KeyError):
    """Raised when a graph builder is not found in the registry."""

    pass


# Global registry of graph builders
_graph_builders: dict[str, Callable[..., Any]] = {}


def register_graph(agent: str, builder: Callable[..., Any]) -> None:
    """Register a graph builder for an agent.

    Args:
        agent: The agent name.
        builder: A callable that returns a compiled graph.
    """
    _graph_builders[agent] = builder


def get_graph_builder(agent: str) -> Callable[..., Any]:
    """Get a graph builder by agent name.

    Args:
        agent: The agent name.

    Returns:
        The builder callable.

    Raises:
        UnknownAgentGraph: If the agent is not registered.
    """
    if agent not in _graph_builders:
        raise UnknownAgentGraph(f"Agent '{agent}' has no registered graph builder")
    return _graph_builders[agent]
