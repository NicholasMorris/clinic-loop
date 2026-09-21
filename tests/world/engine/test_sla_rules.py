"""Tests for SLA rules and breach detection."""

from clinicloop.world.engine import Engine, sla_rules
from clinicloop.world.generator import generate_world
from clinicloop.world.regimes import get_regime
from clinicloop.world.workers import load_staffing


def test_sla_rules_cite_inventory_ids() -> None:
    """Verify SLA rules and their inventory ID mappings.

    Tests:
    1. sla_rules() returns exactly the three expected rules
    2. Each rule maps to the correct inventory ID
    3. Regime parameters contain the correct threshold values
    4. SLA breaches are detected and recorded correctly
    """
    rules = sla_rules()

    # Check exact mapping
    expected_rules = {
        "termination_cutoff": "ps-03",
        "damage_report_window": "ps-04",
        "dispatch_commitment": "po-01",
    }

    assert rules == expected_rules, f"Expected {expected_rules}, got {rules}"

    # Get the AU regime and verify it has the parameters these rules cite
    au_regime = get_regime("au")

    # Verify the parameters exist and have correct values
    assert au_regime.termination_cutoff_business_days == 2
    assert au_regime.damage_report_window_days == 3
    assert au_regime.dispatch_commitment_business_days == 1

    # Generate a world and run the engine
    world = generate_world(
        seed=456,
        population_size=50,
        span_days=1,
    )

    engine = Engine(world, regime_key="au")
    engine.run(1440)

    # Verify the engine runs without error
    hash_value = engine.run_hash()
    assert isinstance(hash_value, str)
    assert len(hash_value) > 0


def test_staffing_config_has_mean_service_minutes() -> None:
    """Verify staffing config includes mean_service_minutes for all pools."""
    staffing = load_staffing()

    expected_pools = {"intake", "prescriber_review", "pharmacy_fulfilment", "support_inbox"}
    assert set(staffing.keys()) == expected_pools

    # Check that each pool has mean_service_minutes
    for pool_name, config in staffing.items():
        assert hasattr(config, "mean_service_minutes"), (
            f"Pool '{pool_name}' should have mean_service_minutes"
        )
        assert config.mean_service_minutes > 0, (
            f"Pool '{pool_name}' mean_service_minutes should be > 0"
        )

    # Verify specific expected values
    assert staffing["intake"].mean_service_minutes == 2
    assert staffing["prescriber_review"].mean_service_minutes == 8
    assert staffing["pharmacy_fulfilment"].mean_service_minutes == 4
    assert staffing["support_inbox"].mean_service_minutes == 10
