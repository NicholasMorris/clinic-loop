"""Message endpoints."""

from fastapi import APIRouter, Depends, HTTPException

from clinicloop.world.generator.build import World

from ..schemas.message import MessageCreate, MessageRead

router = APIRouter(prefix="/messages", tags=["messages"])

# In-memory storage for newly created messages
_messages: dict[str, MessageRead] = {}
_message_counter = 0


def get_world() -> World:
    """Get the world dependency.

    This will be overridden by the app.
    """
    raise NotImplementedError()  # pragma: no cover


@router.get("", response_model=list[MessageRead])
def get_messages(world: World = Depends(get_world)) -> list[MessageRead]:
    """Get all messages from the snapshot and created messages.

    Args:
        world: The loaded world snapshot (injected).

    Returns:
        List of MessageRead schemas.
    """
    snapshot_messages = [
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
    # Add any newly created messages
    created = list(_messages.values())
    return snapshot_messages + created


@router.get("/{message_id}", response_model=MessageRead)
def get_message(message_id: str, world: World = Depends(get_world)) -> MessageRead:
    """Get a message by ID.

    Args:
        message_id: The message identifier.
        world: The loaded world snapshot (injected).

    Returns:
        The MessageRead schema for the message.

    Raises:
        HTTPException: 404 if message not found.
    """
    # Check created messages first
    if message_id in _messages:
        return _messages[message_id]

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
def create_message(payload: MessageCreate, world: World = Depends(get_world)) -> MessageRead:
    """Create a new message.

    Args:
        payload: The MessageCreate request body.
        world: The loaded world snapshot (injected).

    Returns:
        The created MessageRead schema.

    Raises:
        HTTPException: 404 if patient not found.
    """
    global _message_counter

    # Verify patient exists
    patient = next((p for p in world.patients if p.patient_id == payload.patient_id), None)
    if patient is None:
        raise HTTPException(
            status_code=404,
            detail=f"Patient {payload.patient_id} not found",
        )

    # Create new message ID
    _message_counter += 1
    message_id = f"M{_message_counter:06d}"

    # Create the message
    message = MessageRead(
        message_id=message_id,
        patient_id=payload.patient_id,
        channel=payload.channel,
        received_at_minute=0,  # Newly created message
        body=payload.body,
        synthetic=True,
    )

    _messages[message_id] = message
    return message
