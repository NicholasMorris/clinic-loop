"""Consult endpoints."""

from fastapi import APIRouter, Depends, HTTPException

from clinicloop.world.generator.build import World

from ..schemas.consult import ConsultRead

router = APIRouter(prefix="/consults", tags=["consults"])


def get_world() -> World:
    """Get the world dependency.

    This will be overridden by the app.
    """
    raise NotImplementedError()  # pragma: no cover


@router.get("", response_model=list[ConsultRead])
def get_consults(world: World = Depends(get_world)) -> list[ConsultRead]:
    """Get all consults from the snapshot.

    Args:
        world: The loaded world snapshot (injected).

    Returns:
        List of ConsultRead schemas.
    """
    return [
        ConsultRead(
            consult_id=c.consult_id,
            patient_id=c.patient_id,
            questionnaire_id=c.questionnaire_id,
            clinician_id=c.clinician_id,
            scheduled_at_minute=c.scheduled_at_minute,
            duration_minutes=c.duration_minutes,
            mode=c.mode,
            status=c.status,
            synthetic=c.synthetic,
        )
        for c in world.consults
    ]


@router.get("/{consult_id}", response_model=ConsultRead)
def get_consult(consult_id: str, world: World = Depends(get_world)) -> ConsultRead:
    """Get a consult by ID.

    Args:
        consult_id: The consult identifier.
        world: The loaded world snapshot (injected).

    Returns:
        The ConsultRead schema for the consult.

    Raises:
        HTTPException: 404 if consult not found.
    """
    consult = next((c for c in world.consults if c.consult_id == consult_id), None)
    if consult is None:
        raise HTTPException(
            status_code=404,
            detail=f"Consult {consult_id} not found",
        )

    return ConsultRead(
        consult_id=consult.consult_id,
        patient_id=consult.patient_id,
        questionnaire_id=consult.questionnaire_id,
        clinician_id=consult.clinician_id,
        scheduled_at_minute=consult.scheduled_at_minute,
        duration_minutes=consult.duration_minutes,
        mode=consult.mode,
        status=consult.status,
        synthetic=consult.synthetic,
    )
