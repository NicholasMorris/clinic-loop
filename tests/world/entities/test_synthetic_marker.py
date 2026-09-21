"""AC2: Entity models must be frozen and synthetic-only."""

import pytest
from pydantic import ValidationError

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
    # Create minimal valid instances for testing
    patient = Patient(
        patient_id="P000001",
        market="AU",
        full_name="Test Patient",
        date_of_birth="1980-01-01",
        street_address="123 Main St",
        postcode="2000",
        phone_number="0400123456",
        email="test@test.example.com",
        health_identifier="9900000001",
        payment_instrument_id="PI00001",
        created_at_minute=0,
        synthetic=True,
    )

    questionnaire = Questionnaire(
        questionnaire_id="Q000001",
        patient_id="P000001",
        submitted_at_minute=10,
        answers={},
        template_id=None,
        synthetic=True,
    )

    consult = Consult(
        consult_id="C000001",
        patient_id="P000001",
        questionnaire_id="Q000001",
        clinician_id="C01",
        scheduled_at_minute=100,
        duration_minutes=15,
        mode="phone",
        status="scheduled",
        synthetic=True,
    )

    prescription = Prescription(
        prescription_id="RX000001",
        consult_id="C000001",
        patient_id="P000001",
        issued_at_minute=150,
        status="issued",
        synthetic=True,
    )

    order = Order(
        order_id="O000001",
        prescription_id="RX000001",
        patient_id="P000001",
        created_at_minute=200,
        plan_price_cents=5000,
        shipping_cents=995,
        status="created",
        synthetic=True,
    )

    message = Message(
        message_id="M000001",
        patient_id="P000001",
        channel="chat",
        received_at_minute=250,
        body="Test message",
        synthetic=True,
    )

    entities = [patient, questionnaire, consult, prescription, order, message]
    entity_classes = [Patient, Questionnaire, Consult, Prescription, Order, Message]

    # Test 1: All instances have synthetic=True
    for instance in entities:
        assert hasattr(instance, "synthetic")
        assert instance.synthetic is True

    # Test 2: Construction with synthetic=False raises ValidationError
    def test_patient_false() -> None:
        Patient(
            patient_id="P000001",
            market="AU",
            full_name="Test",
            date_of_birth="1980-01-01",
            street_address="123 St",
            postcode="2000",
            phone_number="0400123456",
            email="test@test.example.com",
            health_identifier="9900000001",
            payment_instrument_id="PI00001",
            created_at_minute=0,
            synthetic=False,  # type: ignore
        )

    def test_questionnaire_false() -> None:
        Questionnaire(
            questionnaire_id="Q000001",
            patient_id="P000001",
            submitted_at_minute=10,
            answers={},
            template_id=None,
            synthetic=False,  # type: ignore
        )

    def test_consult_false() -> None:
        Consult(
            consult_id="C000001",
            patient_id="P000001",
            questionnaire_id="Q000001",
            clinician_id="C01",
            scheduled_at_minute=100,
            duration_minutes=15,
            mode="phone",
            status="scheduled",
            synthetic=False,  # type: ignore
        )

    def test_prescription_false() -> None:
        Prescription(
            prescription_id="RX000001",
            consult_id="C000001",
            patient_id="P000001",
            issued_at_minute=150,
            status="issued",
            synthetic=False,  # type: ignore
        )

    def test_order_false() -> None:
        Order(
            order_id="O000001",
            prescription_id="RX000001",
            patient_id="P000001",
            created_at_minute=200,
            plan_price_cents=5000,
            shipping_cents=995,
            status="created",
            synthetic=False,  # type: ignore
        )

    def test_message_false() -> None:
        Message(
            message_id="M000001",
            patient_id="P000001",
            channel="chat",
            received_at_minute=250,
            body="Test message",
            synthetic=False,  # type: ignore
        )

    test_funcs = [
        test_patient_false,
        test_questionnaire_false,
        test_consult_false,
        test_prescription_false,
        test_order_false,
        test_message_false,
    ]
    for test_func in test_funcs:
        with pytest.raises(ValidationError):
            test_func()

    # Test 3: Instances are frozen (immutable)
    for instance in entities:
        with pytest.raises(ValidationError):
            instance.synthetic = False  # type: ignore[assignment]
