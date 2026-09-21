"""Store and retrieve metric snapshots from files."""

import json
from pathlib import Path

from .models import MetricSnapshot


def write_run_snapshot(
    snapshot: MetricSnapshot, seed: int, snapshots_dir: Path | str | None = None
) -> None:
    """Write a MetricSnapshot to a JSON file.

    Args:
        snapshot: The MetricSnapshot to write.
        seed: The seed used for the run.
        snapshots_dir: Directory to write to. Defaults to var/snapshots/.
    """
    if snapshots_dir is None:
        snapshots_dir = Path("var/snapshots")
    else:
        snapshots_dir = Path(snapshots_dir)

    # Create directory if it doesn't exist
    snapshots_dir.mkdir(parents=True, exist_ok=True)

    # Build the file path
    file_path = snapshots_dir / f"run-{seed}.json"

    # Convert snapshot to dict and add seed
    snapshot_dict = snapshot.model_dump()
    snapshot_dict["seed"] = seed

    # Write to file
    with open(file_path, "w") as f:
        json.dump(snapshot_dict, f, indent=2)


def read_run_snapshot(path: Path | str) -> MetricSnapshot:
    """Read a MetricSnapshot from a JSON file.

    Args:
        path: Path to the snapshot file.

    Returns:
        The MetricSnapshot from the file.
    """
    path = Path(path)

    # Read the file
    with open(path, "r") as f:
        data = json.load(f)

    # Remove seed if present (it's not part of the model)
    data.pop("seed", None)

    # Reconstruct SLABreach objects from dicts if needed
    if "sla_breaches" in data and isinstance(data["sla_breaches"], dict):
        from .models import SLABreach

        sla_breaches = {}
        for rule_id, breach_data in data["sla_breaches"].items():
            if isinstance(breach_data, dict):
                sla_breaches[rule_id] = SLABreach(**breach_data)
            else:
                sla_breaches[rule_id] = breach_data
        data["sla_breaches"] = sla_breaches

    # Create MetricSnapshot from data
    return MetricSnapshot(**data)
