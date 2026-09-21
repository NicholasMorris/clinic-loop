"""Registry for metric functions and their thresholds per component."""

from typing import Callable


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
    component: str, name: str, metric_func: Callable, threshold: float
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
    raise NotImplementedError
