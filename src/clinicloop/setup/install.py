"""Setup and installation utilities."""

from pathlib import Path
from typing import List, Optional


def find_binary(name: str) -> Optional[str]:
    """Find a binary in system PATH.

    Args:
        name: Name of the binary to find (e.g. 'ffmpeg').

    Returns:
        Full path to the binary if found, None otherwise.
    """
    raise NotImplementedError


def get_available_memory_gib() -> int:
    """Detect available system memory in GiB.

    Returns:
        Available memory in GiB.
    """
    raise NotImplementedError


def run_package_manager(command: List[str]) -> int:
    """Run a package manager command.

    Args:
        command: Command to run as a list of strings.

    Returns:
        Exit code.
    """
    raise NotImplementedError


def run_setup(
    hardware_tiers_path: str,
    config_path: Optional[Path] = None,
) -> int:
    """Run setup to install dependencies and configure the system.

    Args:
        hardware_tiers_path: Path to hardware_tiers.toml.
        config_path: Optional path to models.toml config file to write.

    Returns:
        Exit code: 0 on success, 1 on failure.
    """
    raise NotImplementedError


def main() -> None:
    """Entry point for clinicloop-install command."""
    raise NotImplementedError
