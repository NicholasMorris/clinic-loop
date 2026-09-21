"""Pydantic schemas for message endpoints."""

from typing import Literal

from pydantic import BaseModel


class MessageCreate(BaseModel):
    """Request schema for creating a message.

    Attributes:
        patient_id: Patient identifier.
        channel: Communication channel (chat or email).
        body: Message text.
        jurisdiction: Optional jurisdiction code (au, uk, nz).
    """

    patient_id: str
    channel: str
    body: str
    jurisdiction: str | None = None


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


class MessageCreated(MessageRead):
    """Response schema for created messages.

    Extends MessageRead with guard verdict information.

    Attributes:
        text_sha256: SHA256 hash of the message body that was checked.
        jurisdiction: The jurisdiction the check was performed against.
        jurisdiction_source: Source of the jurisdiction ("request" or "default_au").
    """

    text_sha256: str
    jurisdiction: str
    jurisdiction_source: Literal["request", "default_au"]
