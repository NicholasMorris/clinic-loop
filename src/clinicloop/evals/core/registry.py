"""Registry for metric functions and their thresholds per component."""

from typing import Any, Callable

# Global registry of metrics: (component, name) -> (metric_func, threshold)
_METRIC_REGISTRY: dict[tuple[str, str], tuple[Callable[..., Any], float]] = {}


class DuplicateMetric(Exception):
    """Raised when a metric is registered twice under the same component and name.

    Attributes:
        component: The component name.
        metric_name: The metric name.
    """

    def __init__(self, component: str, metric_name: str) -> None:
        """Initialize the exception.

        Args:
            component: The component name.
            metric_name: The metric name.
        """
        super().__init__(
            f"Duplicate metric registration: component={component}, metric={metric_name}"
        )
        self.component = component
        self.metric_name = metric_name


def register_metric(
    component: str, name: str, metric_func: Callable[..., Any], threshold: float
) -> None:
    """Register a named metric function and threshold for a component.

    Args:
        component: The component name.
        name: The metric name.
        metric_func: The metric function.
        threshold: The threshold value.

    Raises:
        DuplicateMetric: If the metric is already registered.
    """
    key = (component, name)
    if key in _METRIC_REGISTRY:
        raise DuplicateMetric(component, name)
    _METRIC_REGISTRY[key] = (metric_func, threshold)


def get_metric(
    component: str, name: str
) -> tuple[Callable[..., Any], float] | None:
    """Retrieve a registered metric.

    Args:
        component: The component name.
        name: The metric name.

    Returns:
        A tuple of (metric_func, threshold) or None if not found.
    """
    return _METRIC_REGISTRY.get((component, name))


def clear_registry() -> None:
    """Clear all registered metrics (for testing)."""
    _METRIC_REGISTRY.clear()
