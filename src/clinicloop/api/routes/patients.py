"""Patient endpoints."""

from fastapi import APIRouter, Depends, HTTPException

from clinicloop.world.generator.build import World

from ..schemas.patient import PatientRead

router = APIRouter(prefix="/patients", tags=["patients"])


def get_world() -> World:
    """Get the world dependency.

    This will be overridden by the app.
    """
    raise NotImplementedError()  # pragma: no cover


@router.get("", response_model=list[PatientRead])
def get_patients(world: World = Depends(get_world)) -> list[PatientRead]:
    """Get all patients from the snapshot.

    Args:
        world: The loaded world snapshot (injected).

    Returns:
        List of PatientRead schemas.
    """
    return [
        PatientRead(
            patient_id=p.patient_id,
            market=p.market,
            full_name=p.full_name,
            date_of_birth=p.date_of_birth,
            street_address=p.street_address,
            postcode=p.postcode,
            phone_number=p.phone_number,
            email=p.email,
            health_identifier=p.health_identifier,
            payment_instrument_id=p.payment_instrument_id,
            created_at_minute=p.created_at_minute,
            synthetic=p.synthetic,
        )
        for p in world.patients
    ]


@router.get("/{patient_id}", response_model=PatientRead)
def get_patient(patient_id: str, world: World = Depends(get_world)) -> PatientRead:
    """Get a patient by ID.

    Args:
        patient_id: The patient identifier.
        world: The loaded world snapshot (injected).

    Returns:
        The PatientRead schema for the patient.

    Raises:
        HTTPException: 404 if patient not found.
    """
    patient = next((p for p in world.patients if p.patient_id == patient_id), None)
    if patient is None:
        raise HTTPException(
            status_code=404,
            detail=f"Patient {patient_id} not found",
        )

    return PatientRead(
        patient_id=patient.patient_id,
        market=patient.market,
        full_name=patient.full_name,
        date_of_birth=patient.date_of_birth,
        street_address=patient.street_address,
        postcode=patient.postcode,
        phone_number=patient.phone_number,
        email=patient.email,
        health_identifier=patient.health_identifier,
        payment_instrument_id=patient.payment_instrument_id,
        created_at_minute=patient.created_at_minute,
        synthetic=patient.synthetic,
    )
