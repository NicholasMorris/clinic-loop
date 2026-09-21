"""Entity models for SimClinic world."""

from typing import Literal

from pydantic import BaseModel, ConfigDict


class Patient(BaseModel):
    """Patient entity."""

    model_config = ConfigDict(frozen=True)

    synthetic: Literal[True]


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
