"""Pydantic schemas for consult endpoints."""

from pydantic import BaseModel


class ConsultRead(BaseModel):
    """Response schema for consult reads.

    Attributes:
        consult_id: Consult identifier.
        patient_id: Patient identifier.
        questionnaire_id: Questionnaire identifier.
        clinician_id: Clinician identifier.
        scheduled_at_minute: Scheduled time in sim-minutes.
        duration_minutes: Planned duration.
        mode: Consultation mode.
        status: Consult status.
        synthetic: Always True.
    """

    consult_id: str
    patient_id: str
    questionnaire_id: str
    clinician_id: str
    scheduled_at_minute: int
    duration_minutes: int
    mode: str
    status: str
    synthetic: bool
