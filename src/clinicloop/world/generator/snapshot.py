"""World snapshot serialization and deserialization."""

import json
from pathlib import Path

from ..entities import Consult, Message, Order, Patient, Prescription, Questionnaire
from .build import World


def write_world_snapshot(
    world: World,
    path: Path | str,
) -> None:
    """Serialize a world to JSON with full population data.

    Creates a JSON file containing the world metadata (schema_version, seed,
    population_size, span_days) and the complete population of all entities,
    sorted canonically for digest stability.

    The snapshot format is canonical JSON:
    - Keys are sorted alphabetically
    - No extra whitespace
    - Deterministic across processes and seeds

    Args:
        world: The World to serialize.
        path: Path to write the JSON file.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Build the snapshot with full population data
    snapshot: dict[str, object] = {
        "schema_version": "1",
        "seed": world.seed,
        "population_size": world.population_size,
        "span_days": world.span_days,
        "patients": sorted(
            [_serialize_entity(p) for p in world.patients],
            key=lambda x: str(x["patient_id"]),
        ),
        "questionnaires": sorted(
            [_serialize_entity(q) for q in world.questionnaires],
            key=lambda x: str(x["questionnaire_id"]),
        ),
        "consults": sorted(
            [_serialize_entity(c) for c in world.consults],
            key=lambda x: str(x["consult_id"]),
        ),
        "prescriptions": sorted(
            [_serialize_entity(p) for p in world.prescriptions],
            key=lambda x: str(x["prescription_id"]),
        ),
        "orders": sorted(
            [_serialize_entity(o) for o in world.orders],
            key=lambda x: str(x["order_id"]),
        ),
        "messages": sorted(
            [_serialize_entity(m) for m in world.messages],
            key=lambda x: str(x["message_id"]),
        ),
    }

    # Write with canonical JSON formatting (sorted keys, no whitespace)
    with open(path, "w") as f:
        json.dump(snapshot, f, separators=(",", ":"), sort_keys=True)


def read_world_snapshot(path: Path | str) -> World:
    """Deserialize a world from JSON.

    Reads a JSON snapshot file and reconstructs the World object with full
    population data. This is not regeneration; entities are read directly
    from the snapshot.

    Args:
        path: Path to read the JSON file.

    Returns:
        The deserialized World with all entities.

    Raises:
        ValueError: If schema version is unsupported.
        KeyError: If required fields are missing.
    """
    path = Path(path)

    with open(path) as f:
        snapshot = json.load(f)

    # Validate schema version
    schema_version = snapshot.get("schema_version")
    if schema_version != "1":
        raise ValueError(f"Unsupported schema version: {schema_version}")

    # Extract metadata
    seed = snapshot["seed"]
    population_size = snapshot["population_size"]
    span_days = snapshot["span_days"]

    # Deserialize all entities from snapshot
    patients = [Patient(**p) for p in snapshot["patients"]]
    questionnaires = [Questionnaire(**q) for q in snapshot["questionnaires"]]
    consults = [Consult(**c) for c in snapshot["consults"]]
    prescriptions = [Prescription(**p) for p in snapshot["prescriptions"]]
    orders = [Order(**o) for o in snapshot["orders"]]
    messages = [Message(**m) for m in snapshot["messages"]]

    return World(
        patients=patients,
        questionnaires=questionnaires,
        consults=consults,
        prescriptions=prescriptions,
        orders=orders,
        messages=messages,
        seed=seed,
        population_size=population_size,
        span_days=span_days,
    )


def _serialize_entity(entity: Patient | Questionnaire | Consult | Prescription | Order | Message) -> dict[str, object]:
    """Convert a pydantic entity to a serializable dict.

    Args:
        entity: A pydantic model instance.

    Returns:
        A dictionary representation of the entity.
    """
    return entity.model_dump()
