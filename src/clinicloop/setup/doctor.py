"""System configuration checker (doctor command)."""

from pathlib import Path
from typing import Optional


def find_binary(name: str) -> Optional[str]:
    """Find a binary in system PATH.

    Args:
        name: Name of the binary to find (e.g. 'ffmpeg').

    Returns:
        Full path to the binary if found, None otherwise.
    """
    raise NotImplementedError


def get_binary_version(binary_path: str) -> str:
    """Get version string from a binary.

    Args:
        binary_path: Full path to the binary.

    Returns:
        Version string.
    """
    raise NotImplementedError


def get_available_memory_gib() -> int:
    """Detect available system memory in GiB.

    Returns:
        Available memory in GiB.
    """
    raise NotImplementedError


def run_doctor(
    hardware_tiers_path: str,
    config_path: Optional[Path] = None,
) -> int:
    """Check system configuration and report status.

    Args:
        hardware_tiers_path: Path to hardware_tiers.toml.
        config_path: Optional path to models.toml config file to read.

    Returns:
        Exit code: 0 if all checks pass, 1 if any checks fail.
    """
    raise NotImplementedError


def main() -> None:
    """Entry point for clinicloop-doctor command."""
    raise NotImplementedError
