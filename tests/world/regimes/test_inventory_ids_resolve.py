"""AC5: Inventory IDs validation and manifest."""

import re

import pytest

from clinicloop.world.regimes import KNOWN_INVENTORY_IDS, get_regime


@pytest.mark.checklist_id("AC5")
def test_every_parameter_cites_a_manifest_inventory_id() -> None:
    """Test that every regime parameter cites valid inventory IDs.

    Verifies that:
    1. KNOWN_INVENTORY_IDS contains at least ps-03, ps-04, po-01, po-02, po-06, x-01
    2. Every regime parameter carries an inventory_ids tuple
    3. Every id matches pattern ^(ps|cp|po|x)-[0-9]{2}$
    4. Every id is a member of KNOWN_INVENTORY_IDS
    """
    # Check that KNOWN_INVENTORY_IDS contains required entries
    required_ids = {"ps-03", "ps-04", "po-01", "po-02", "po-06", "x-01"}
    assert required_ids.issubset(
        KNOWN_INVENTORY_IDS
    ), f"KNOWN_INVENTORY_IDS missing required IDs: {required_ids - KNOWN_INVENTORY_IDS}"

    # Pattern for valid inventory IDs
    id_pattern = re.compile(r"^(ps|cp|po|x)-\d{2}$")

    # Verify all IDs in the manifest match the pattern
    for inventory_id in KNOWN_INVENTORY_IDS:
        assert id_pattern.match(inventory_id), f"Inventory ID {inventory_id} doesn't match pattern"

    # Get AU regime and verify its parameters cite valid inventory IDs
    au = get_regime("au")

    # Collect all inventory_ids from parameters
    all_cited_ids = set()
    for param_name, (value, ids) in au._params.items():
        assert isinstance(ids, tuple), f"Parameter {param_name} ids should be a tuple"
        assert len(ids) >= 1, f"Parameter {param_name} must cite at least one inventory ID"
        for inventory_id in ids:
            assert id_pattern.match(
                inventory_id
            ), f"Parameter {param_name} cites invalid ID {inventory_id}"
            assert inventory_id in KNOWN_INVENTORY_IDS, (
                f"Parameter {param_name} cites unknown ID {inventory_id}"
            )
            all_cited_ids.add(inventory_id)

    # Collect inventory_ids from recorded conflicts
    for conflict in au.recorded_conflicts:
        all_cited_ids.add(conflict.inventory_id)

    # Verify at least the required IDs are cited or in conflicts
    assert required_ids.issubset(
        all_cited_ids
    ), f"Not all required IDs are cited or in conflicts: {required_ids - all_cited_ids}"
