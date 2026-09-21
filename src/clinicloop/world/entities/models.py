"""Entity models for SimClinic world."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Patient(BaseModel):
    """Patient entity with demographic and contact information.

    Attributes:
        patient_id: Zero-padded patient identifier (P000001...).
        market: Market jurisdiction (AU, NZ, or UK).
        full_name: Fictional name combining first and family names.
        date_of_birth: ISO date string (adults only).
        street_address: Fictional street address.
        postcode: Fictional postal code.
        phone_number: Fictional phone number from fictional ranges.
        email: Email address with fictional domain.
        health_identifier: Fictional health identifier from fictional ranges.
        payment_instrument_id: Opaque identifier (PI00042...).
        created_at_minute: Creation time in sim-minutes since world t0.
        synthetic: Always True (frozen marker).
    """

    model_config = ConfigDict(frozen=True)

    patient_id: str
    market: Literal["AU", "NZ", "UK"]
    full_name: str
    date_of_birth: str  # ISO date string
    street_address: str
    postcode: str
    phone_number: str
    email: str
    health_identifier: str
    payment_instrument_id: str
    created_at_minute: int
    synthetic: Literal[True]


class Questionnaire(BaseModel):
    """Questionnaire entity with patient-submitted information.

    Attributes:
        questionnaire_id: Zero-padded questionnaire identifier.
        patient_id: Reference to patient.
        submitted_at_minute: Submission time in sim-minutes.
        answers: Free-text answers keyed by field name.
        template_id: Reference to shared template if any, else None.
        synthetic: Always True (frozen marker).
    """

    model_config = ConfigDict(frozen=True)

    questionnaire_id: str
    patient_id: str
    submitted_at_minute: int
    answers: dict[str, str]
    template_id: str | None
    synthetic: Literal[True]


class Consult(BaseModel):
    """Consult entity representing a scheduled clinical consultation.

    Attributes:
        consult_id: Zero-padded consult identifier.
        patient_id: Reference to patient.
        questionnaire_id: Reference to questionnaire.
        clinician_id: Reference to clinician (C01..C06).
        scheduled_at_minute: Scheduled time in sim-minutes.
        duration_minutes: Planned duration (10 to 30 minutes).
        mode: Consultation mode (currently 'phone').
        status: Consult status (currently 'scheduled').
        synthetic: Always True (frozen marker).
    """

    model_config = ConfigDict(frozen=True)

    consult_id: str
    patient_id: str
    questionnaire_id: str
    clinician_id: str
    scheduled_at_minute: int
    duration_minutes: int
    mode: Literal["phone"]
    status: Literal["scheduled"]
    synthetic: Literal[True]


class Prescription(BaseModel):
    """Prescription entity for approved items.

    Attributes:
        prescription_id: Zero-padded prescription identifier.
        consult_id: Reference to consult.
        patient_id: Reference to patient.
        issued_at_minute: Issue time in sim-minutes.
        status: Prescription status (currently 'issued').
        synthetic: Always True (frozen marker).
    """

    model_config = ConfigDict(frozen=True)

    prescription_id: str
    consult_id: str
    patient_id: str
    issued_at_minute: int
    status: Literal["issued"]
    synthetic: Literal[True]


class Order(BaseModel):
    """Order entity for pharmacy fulfillment.

    Attributes:
        order_id: Zero-padded order identifier.
        prescription_id: Reference to prescription.
        patient_id: Reference to patient.
        created_at_minute: Creation time in sim-minutes.
        plan_price_cents: Price in cents.
        shipping_cents: Shipping cost in cents (market-dependent).
        status: Order status (currently 'created').
        synthetic: Always True (frozen marker).
    """

    model_config = ConfigDict(frozen=True)

    order_id: str
    prescription_id: str
    patient_id: str
    created_at_minute: int
    plan_price_cents: int
    shipping_cents: int
    status: Literal["created"]
    synthetic: Literal[True]


class Message(BaseModel):
    """Message entity for patient-clinician communication.

    Attributes:
        message_id: Zero-padded message identifier.
        patient_id: Reference to patient.
        channel: Communication channel ('chat' or 'email').
        received_at_minute: Receipt time in sim-minutes.
        body: Message text from templates.
        synthetic: Always True (frozen marker).
    """

    model_config = ConfigDict(frozen=True)

    message_id: str
    patient_id: str
    channel: Literal["chat", "email"]
    received_at_minute: int
    body: str
    synthetic: Literal[True]
