"""AC2: Entity models must be frozen and synthetic-only."""

import pytest

from clinicloop.world.entities import (
    Consult,
    Message,
    Order,
    Patient,
    Prescription,
    Questionnaire,
)


@pytest.mark.checklist_id("AC2")
def test_entities_are_frozen_and_synthetic_only() -> None:
    """Test that all six entity types are frozen and synthetic-only.

    All entity models must:
    1. Be frozen (immutable)
    2. Have a synthetic: Literal[True] field
    3. Reject construction with synthetic=False
    4. Reject field assignment on a built instance
    """
    entity_classes = [
        Patient,
        Questionnaire,
        Consult,
        Prescription,
        Order,
        Message,
    ]

    for entity_cls in entity_classes:
        # Test 1: Construction with synthetic=True succeeds
        instance = entity_cls(synthetic=True)
        assert instance.synthetic is True

        # Test 2: Construction with synthetic=False raises ValidationError
        with pytest.raises(ValueError):
            entity_cls(synthetic=False)  # type: ignore

        # Test 3: Instance is frozen (immutable)
        with pytest.raises(Exception):  # pydantic.ValidationError for frozen models
            instance.synthetic = False  # type: ignore
