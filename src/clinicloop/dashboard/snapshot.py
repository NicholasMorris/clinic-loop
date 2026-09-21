"""Snapshot writer for dashboard."""

from clinicloop.dashboard.runner import write_default_snapshot


def main() -> None:
    """Write default snapshot and print the path."""
    write_default_snapshot()
    from clinicloop.dashboard.runner import snapshot_path

    print(snapshot_path())


if __name__ == "__main__":
    main()
