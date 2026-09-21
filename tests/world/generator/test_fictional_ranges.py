"""AC7: Fictional ranges for identifiers."""

import pytest

from clinicloop.world.generator import generate_world


@pytest.mark.checklist_id("AC7")
def test_identifiers_fall_in_declared_fictional_ranges() -> None:
    """Test that all generated identifiers fall within fictional ranges.

    Verifies that every generated phone number, email domain, and health-identifier
    value falls inside the fictional ranges declared as constants in
    world/generator/fictional_ranges.py and documented in docs/world/entities.md.
    """
    world = generate_world(seed=20260921, population_size=500, span_days=30)

    # This test is a stub that will be implemented after the fictional ranges
    # mechanism is built.
    pytest.skip("Fictional ranges mechanism not yet implemented")
