"""Message endpoints."""

from typing import cast

from fastapi import APIRouter, Depends, HTTPException, Request

from clinicloop.world.generator.build import World

from ..schemas.message import MessageCreate, MessageRead

router = APIRouter(prefix="/messages", tags=["messages"])


def get_world() -> World:
    """Get the world dependency.

    This will be overridden by the app.
    """
    raise NotImplementedError()  # pragma: no cover


@router.get("", response_model=list[MessageRead])
def get_messages(world: World = Depends(get_world)) -> list[MessageRead]:
    """Get all messages from the snapshot.

    Args:
        world: The loaded world snapshot (injected).

    Returns:
        List of MessageRead schemas.
    """
    return [
        MessageRead(
            message_id=m.message_id,
            patient_id=m.patient_id,
            channel=m.channel,
            received_at_minute=m.received_at_minute,
            body=m.body,
            synthetic=m.synthetic,
        )
        for m in world.messages
    ]


@router.get("/{message_id}", response_model=MessageRead)
def get_message(
    message_id: str,
    request: Request,
    world: World = Depends(get_world),
) -> MessageRead:
    """Get a message by ID.

    Args:
        message_id: The message identifier.
        world: The loaded world snapshot (injected).
        request: The request object (for accessing app state).

    Returns:
        The MessageRead schema for the message.

    Raises:
        HTTPException: 404 if message not found.
    """
    # Check created messages first
    if message_id in request.app.state.created_messages:
        return cast(MessageRead, request.app.state.created_messages[message_id])

    # Check snapshot messages
    message = next((m for m in world.messages if m.message_id == message_id), None)
    if message is None:
        raise HTTPException(
            status_code=404,
            detail=f"Message {message_id} not found",
        )

    return MessageRead(
        message_id=message.message_id,
        patient_id=message.patient_id,
        channel=message.channel,
        received_at_minute=message.received_at_minute,
        body=message.body,
        synthetic=message.synthetic,
    )


@router.post("", response_model=MessageRead, status_code=201)
def create_message(
    request: Request,
    payload: MessageCreate,
    world: World = Depends(get_world),
) -> MessageRead:
    """Create a new message.

    Args:
        payload: The MessageCreate request body.
        world: The loaded world snapshot (injected).
        request: The request object (for accessing app state).

    Returns:
        The created MessageRead schema.

    Raises:
        HTTPException: 404 if patient not found.
    """
    # Verify patient exists
    patient = next((p for p in world.patients if p.patient_id == payload.patient_id), None)
    if patient is None:
        raise HTTPException(
            status_code=404,
            detail=f"Patient {payload.patient_id} not found",
        )

    # Create new message ID
    request.app.state.message_counter += 1
    message_id = f"M{request.app.state.message_counter:06d}"

    # Create the message
    message = MessageRead(
        message_id=message_id,
        patient_id=payload.patient_id,
        channel=payload.channel,
        received_at_minute=0,  # Newly created message
        body=payload.body,
        synthetic=True,
    )

    request.app.state.created_messages[message_id] = message
    return message
