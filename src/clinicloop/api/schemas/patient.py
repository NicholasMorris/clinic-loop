"""Pydantic schemas for patient endpoints."""

from pydantic import BaseModel


class PatientRead(BaseModel):
    """Response schema for patient reads.

    Attributes:
        patient_id: Patient identifier.
        market: Market jurisdiction (AU, NZ, UK).
        full_name: Patient's full name.
        date_of_birth: ISO date string.
        street_address: Street address.
        postcode: Postal code.
        phone_number: Phone number.
        email: Email address.
        health_identifier: Health identifier.
        payment_instrument_id: Payment instrument identifier.
        created_at_minute: Creation time in sim-minutes.
        synthetic: Always True.
    """

    patient_id: str
    market: str
    full_name: str
    date_of_birth: str
    street_address: str
    postcode: str
    phone_number: str
    email: str
    health_identifier: str
    payment_instrument_id: str
    created_at_minute: int
    synthetic: bool
