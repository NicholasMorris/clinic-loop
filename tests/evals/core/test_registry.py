"""AC1: Registry for metric functions with duplicate detection."""

import pytest

from clinicloop.evals.core.registry import DuplicateMetric, register_metric


@pytest.mark.checklist_id("E2")
def test_duplicate_metric_registration_raises() -> None:
    """Test that registering duplicate metrics raises DuplicateMetric with component and name."""
    # Define a simple metric function
    def dummy_metric() -> float:
        return 0.5

    component = "test_component"
    metric_name = "test_metric"

    # Register the metric once (should succeed)
    register_metric(component, metric_name, dummy_metric, 0.8)

    # Register the same metric again (should raise)
    with pytest.raises(DuplicateMetric) as exc_info:
        register_metric(component, metric_name, dummy_metric, 0.8)

    # Check that the exception message contains both component and metric name
    assert component in str(exc_info.value)
    assert metric_name in str(exc_info.value)
