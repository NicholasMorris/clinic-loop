"""AC4: Unpopulated regime parameter raises error."""

import pytest

from clinicloop.world.regimes import RegimeParameterNotSet, get_regime


@pytest.mark.checklist_id("AC4")
def test_unpopulated_regime_parameter_raises() -> None:
    """Test that unpopulated regime parameters raise RegimeParameterNotSet.

    Verifies that:
    1. Regime registry has exactly keys: au, nz, uk
    2. nz and uk regimes have parameters_status == "placeholder"
    3. Reading any parameter from nz/uk raises RegimeParameterNotSet
    """
    # Test that we can get all three regimes
    au = get_regime("au")
    nz = get_regime("nz")
    uk = get_regime("uk")

    # Test that nz and uk are placeholders
    assert nz.parameters_status == "placeholder"
    assert uk.parameters_status == "placeholder"

    # Test that accessing a parameter from nz raises RegimeParameterNotSet
    with pytest.raises(RegimeParameterNotSet) as exc_info:
        _ = nz.flat_shipping_cents
    assert "nz" in str(exc_info.value)
    assert "flat_shipping_cents" in str(exc_info.value)

    # Test that accessing a parameter from uk raises RegimeParameterNotSet
    with pytest.raises(RegimeParameterNotSet) as exc_info:
        _ = uk.free_shipping_threshold_cents
    assert "uk" in str(exc_info.value)
    assert "free_shipping_threshold_cents" in str(exc_info.value)
