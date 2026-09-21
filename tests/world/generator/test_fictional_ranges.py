"""AC7: Fictional ranges for identifiers."""

import pytest

from clinicloop.world.generator import generate_world
from clinicloop.world.generator.fictional_ranges import (
    EMAIL_DOMAIN_FICTIONAL,
    HEALTH_ID_FICTIONAL_RANGE,
    HEALTH_ID_PREFIX_FICTIONAL,
    PHONE_AREA_CODE_FICTIONAL,
    PHONE_AREA_CODE_FICTIONAL_RANGE,
)


@pytest.mark.checklist_id("AC7")
def test_identifiers_fall_in_declared_fictional_ranges() -> None:
    """Test that all generated identifiers fall within fictional ranges.

    Verifies that every generated phone number, email domain, and health-identifier
    value falls inside the fictional ranges declared as constants in
    world/generator/fictional_ranges.py and documented in docs/world/entities.md.
    """
    world = generate_world(seed=20260921, population_size=500, span_days=30)

    # Check that all patients have identifiers within fictional ranges
    for patient in world.patients:
        assert patient.phone_number is not None
        assert patient.email_domain is not None
        assert patient.health_identifier is not None

        # Verify phone number is in fictional range
        assert patient.phone_number.startswith(PHONE_AREA_CODE_FICTIONAL), (
            f"Phone {patient.phone_number} doesn't start with {PHONE_AREA_CODE_FICTIONAL}"
        )

        # Verify email domain is the declared fictional domain
        assert patient.email_domain == EMAIL_DOMAIN_FICTIONAL, (
            f"Email domain {patient.email_domain} is not {EMAIL_DOMAIN_FICTIONAL}"
        )

        # Verify health identifier uses fictional prefix
        assert patient.health_identifier.startswith(HEALTH_ID_PREFIX_FICTIONAL), (
            f"Health ID {patient.health_identifier} doesn't start with {HEALTH_ID_PREFIX_FICTIONAL}"
        )
