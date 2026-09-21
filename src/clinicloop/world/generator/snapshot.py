"""World snapshot serialization and deserialization."""

import json
from pathlib import Path

from .build import World


def write_world_snapshot(
    world: World,
    path: Path | str,
) -> None:
    """Serialize a world to JSON.

    Creates a JSON file containing the world metadata (schema_version, seed,
    population_size, span_days) and entity counts. The snapshot format includes
    versioning to support future schema evolution.

    Args:
        world: The World to serialize.
        path: Path to write the JSON file.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    snapshot = {
        "schema_version": "1",
        "seed": world.seed,
        "population_size": world.population_size,
        "span_days": world.span_days,
        "entities": {
            "patients": len(world.patients),
            "questionnaires": len(world.questionnaires),
            "consults": len(world.consults),
            "prescriptions": len(world.prescriptions),
            "orders": len(world.orders),
            "messages": len(world.messages),
        },
    }

    with open(path, "w") as f:
        json.dump(snapshot, f, separators=(",", ":"))


def read_world_snapshot(path: Path | str) -> World:
    """Deserialize a world from JSON.

    Reads a JSON snapshot file and reconstructs the World object. Note that
    the actual entity data is not persisted to disk; only metadata is stored.
    To obtain a world identical to the original, call generate_world with the
    same seed, population_size, and span_days.

    Args:
        path: Path to read the JSON file.

    Returns:
        The deserialized World metadata (entities are empty, must regenerate).
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

    # Note: We don't deserialize the entity counts back to entity lists.
    # To get the actual entities, call generate_world with the same parameters.
    # This ensures reproducibility and avoids storing entity data.
    from .build import generate_world

    return generate_world(
        seed=seed,
        population_size=population_size,
        span_days=span_days,
    )
