"""Store and retrieve metric snapshots from files."""

from pathlib import Path

from .models import MetricSnapshot


def write_run_snapshot(
    snapshot: MetricSnapshot,
    seed: int,
    snapshots_dir: Path | str | None = None
) -> None:
    """Write a MetricSnapshot to a JSON file.

    Args:
        snapshot: The MetricSnapshot to write.
        seed: The seed used for the run.
        snapshots_dir: Directory to write to. Defaults to var/snapshots/.

    Raises:
        NotImplementedError: This function is not yet implemented.
    """
    raise NotImplementedError("write_run_snapshot is not yet implemented")


def read_run_snapshot(path: Path | str) -> MetricSnapshot:
    """Read a MetricSnapshot from a JSON file.

    Args:
        path: Path to the snapshot file.

    Returns:
        The MetricSnapshot from the file.

    Raises:
        NotImplementedError: This function is not yet implemented.
    """
    raise NotImplementedError("read_run_snapshot is not yet implemented")
