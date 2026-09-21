"""Entity models for SimClinic world."""

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict


class Patient(BaseModel):
    """Patient entity."""

    model_config = ConfigDict(frozen=True)

    synthetic: Literal[True]
    phone_number: Optional[str] = None
    email_domain: Optional[str] = None
    health_identifier: Optional[str] = None


class Questionnaire(BaseModel):
    """Questionnaire entity."""

    model_config = ConfigDict(frozen=True)

    synthetic: Literal[True]


class Consult(BaseModel):
    """Consult entity."""

    model_config = ConfigDict(frozen=True)

    synthetic: Literal[True]


class Prescription(BaseModel):
    """Prescription entity."""

    model_config = ConfigDict(frozen=True)

    synthetic: Literal[True]


class Order(BaseModel):
    """Order entity."""

    model_config = ConfigDict(frozen=True)

    synthetic: Literal[True]


class Message(BaseModel):
    """Message entity."""

    model_config = ConfigDict(frozen=True)

    synthetic: Literal[True]
