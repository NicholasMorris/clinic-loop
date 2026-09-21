"""Message endpoints."""

from typing import cast

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from clinicloop.world.generator.build import World

from ..guard_boundary import JURISDICTION_SOURCE_HEADER, enforce_guard
from ..schemas.message import MessageCreate, MessageCreated, MessageRead

router = APIRouter(prefix="/messages", tags=["messages"])


def get_world() -> World:
    """Get the world dependency.

    This will be overridden by the app.
    """
    raise NotImplementedError()  # pragma: no cover


@router.get("", response_model=list[MessageRead])
def get_messages(
    request: Request,
    world: World = Depends(get_world),
) -> list[MessageRead]:
    """Get all messages from the snapshot and created messages.

    Args:
        request: The request object (for accessing app state).
        world: The loaded world snapshot (injected).

    Returns:
        List of MessageRead schemas including both snapshot and created messages.
    """
    # Collect world messages
    messages = [
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

    # Add created messages from this app instance
    messages.extend(request.app.state.created_messages.values())

    return messages


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


@router.post("", status_code=201, dependencies=[Depends(enforce_guard)])
def create_message(
    request: Request,
    payload: MessageCreate,
    world: World = Depends(get_world),
) -> JSONResponse:
    """Create a new message.

    Args:
        payload: The MessageCreate request body.
        world: The loaded world snapshot (injected).
        request: The request object (for accessing app state).

    Returns:
        JSONResponse with the created message and the jurisdiction_source header.

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

    # Get the guard decision from request state (set by enforce_guard dependency)
    guard_decision = request.state.guard_decision

    # Create new message ID
    request.app.state.message_counter += 1
    message_id = f"M{request.app.state.message_counter:06d}"

    # Create the message with guard verdict information
    message = MessageCreated(
        message_id=message_id,
        patient_id=payload.patient_id,
        channel=payload.channel,
        received_at_minute=0,  # Newly created message
        body=payload.body,
        synthetic=True,
        text_sha256=guard_decision.verdict.text_sha256,
        jurisdiction=guard_decision.jurisdiction,
        jurisdiction_source=guard_decision.jurisdiction_source,
    )

    request.app.state.created_messages[message_id] = message

    # Return JSONResponse with header set
    return JSONResponse(
        content=message.model_dump(),
        status_code=201,
        headers={JURISDICTION_SOURCE_HEADER: guard_decision.jurisdiction_source},
    )
