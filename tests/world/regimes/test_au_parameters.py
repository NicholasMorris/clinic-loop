"""AC3: AU regime parameters and recorded conflicts."""

import pytest

from clinicloop.world.regimes import get_regime


@pytest.mark.checklist_id("AC3")
def test_au_parameter_values_and_recorded_conflict() -> None:
    """Test that AU regime has correct parameter values and recorded conflicts.

    Verifies that:
    1. AU regime exposes specific financial and operational parameters
    2. AU regime records the x-01 delivery-time conflict with alternative values
    """
    au = get_regime("au")

    # Check parameter values
    assert au.flat_shipping_cents == 995
    assert au.free_shipping_threshold_cents == 12900
    assert au.termination_cutoff_business_days == 2
    assert au.damage_report_window_days == 3
    assert au.consultation_validity_months == 6
    assert au.delivery_working_days == (4, 5)
    assert au.dispatch_commitment_business_days == 1

    # Check recorded conflict for x-01
    assert hasattr(au, "recorded_conflicts")
    conflicts = au.recorded_conflicts
    assert len(conflicts) >= 1

    # Find the x-01 conflict
    x01_conflict = None
    for conflict in conflicts:
        if conflict.inventory_id == "x-01":
            x01_conflict = conflict
            break

    assert x01_conflict is not None, "x-01 conflict not found in AU recorded_conflicts"
    assert x01_conflict.alternative_value == (2, 5)
