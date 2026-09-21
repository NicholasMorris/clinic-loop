"""Pydantic schemas for message endpoints."""

from pydantic import BaseModel


class MessageCreate(BaseModel):
    """Request schema for creating a message.

    Attributes:
        patient_id: Patient identifier.
        channel: Communication channel (chat or email).
        body: Message text.
    """

    patient_id: str
    channel: str
    body: str


class MessageRead(BaseModel):
    """Response schema for message reads.

    Attributes:
        message_id: Message identifier.
        patient_id: Patient identifier.
        channel: Communication channel.
        received_at_minute: Receipt time in sim-minutes.
        body: Message text.
        synthetic: Always True.
    """

    message_id: str
    patient_id: str
    channel: str
    received_at_minute: int
    body: str
    synthetic: bool
