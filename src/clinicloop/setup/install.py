"""Setup and installation utilities."""

import platform
import shutil
import subprocess
from pathlib import Path

from .tiers import get_available_memory_gib, load_tiers, resolve_tier


def find_binary(name: str) -> str | None:
    """Find a binary in system PATH.

    Args:
        name: Name of the binary to find (e.g. 'ffmpeg').

    Returns:
        Full path to the binary if found, None otherwise.
    """
    # Map common binary names to actual names in PATH
    if name == "whisper.cpp":
        # whisper.cpp 1.9 installs "whisper-cli"; older builds used "whisper-cpp" or "main".
        for candidate in ("whisper-cli", "whisper-cpp", "whisper"):
            result = shutil.which(candidate)
            if result:
                return result
        return None

    return shutil.which(name)


def run_package_manager(command: list[str]) -> int:
    """Run a package manager command.

    Args:
        command: Command to run as a list of strings.

    Returns:
        Exit code.
    """
    try:
        result = subprocess.run(command, check=False)
        return result.returncode
    except Exception as e:
        print(f"Error running package manager: {e}")
        return 1


def _get_install_command_for_ffmpeg() -> list[str] | None:
    """Get the package manager command to install ffmpeg.

    Returns:
        Command list or None if package manager not detected.
    """
    system = platform.system()

    if system == "Darwin":
        # macOS - try brew
        if shutil.which("brew"):
            return ["brew", "install", "ffmpeg"]
    elif system == "Linux":
        # Linux - try apt, dnf, or pacman
        if shutil.which("apt-get"):
            return ["sudo", "apt-get", "install", "-y", "ffmpeg"]
        elif shutil.which("dnf"):
            return ["sudo", "dnf", "install", "-y", "ffmpeg"]
        elif shutil.which("pacman"):
            return ["sudo", "pacman", "-S", "--noconfirm", "ffmpeg"]

    return None


def run_setup(
    hardware_tiers_path: str,
    config_path: Path | None = None,
) -> int:
    """Run setup to install dependencies and configure the system.

    Args:
        hardware_tiers_path: Path to hardware_tiers.toml.
        config_path: Optional path to models.toml config file to write.

    Returns:
        Exit code: 0 on success, 1 on failure.
    """
    # Detect memory and select tier
    try:
        memory_gib = get_available_memory_gib()
        print(f"Detected {memory_gib} GiB memory")

        tiers_path = Path(hardware_tiers_path)
        tiers = load_tiers(tiers_path)
        selected_tier = resolve_tier(tiers)
        print(f"Selected tier: {selected_tier['label']}")
    except Exception as e:
        print(f"ERROR: Could not select hardware tier: {e}")
        return 1

    # Check and install ffmpeg if needed
    ffmpeg_path = find_binary("ffmpeg")
    if not ffmpeg_path:
        print("ffmpeg not found, attempting to install...")
        install_cmd = _get_install_command_for_ffmpeg()
        if install_cmd:
            print(f"Running: {' '.join(install_cmd)}")
            if run_package_manager(install_cmd) != 0:
                print("WARNING: ffmpeg installation may have failed")
        else:
            print("WARNING: Could not determine how to install ffmpeg on this system")
    else:
        print(f"ffmpeg found at {ffmpeg_path}")

    # Check whisper.cpp and print build instructions if missing
    whisper_path = find_binary("whisper.cpp")
    if not whisper_path:
        print("\nwhisper.cpp binary not found.")
        print("To build whisper.cpp, run:")
        print("  git clone https://github.com/ggerganov/whisper.cpp.git")
        print("  cd whisper.cpp")
        print("  make main")
        print("  # Add to PATH or copy to /usr/local/bin")
    else:
        print(f"whisper.cpp found at {whisper_path}")

    # Write configuration
    if config_path is None:
        # Default to ~/.config/clinicloop/models.toml
        config_path = Path.home() / ".config" / "clinicloop" / "models.toml"

    config_path.parent.mkdir(parents=True, exist_ok=True)

    config_data = {
        "model": {
            "tier": selected_tier["label"],
            "repo_id": selected_tier["repo_id"],
            "quantisation": selected_tier["quantisation"],
        }
    }

    # Write as TOML format
    toml_content = "[model]\n"
    toml_content += f'tier = "{config_data["model"]["tier"]}"\n'
    toml_content += f'repo_id = "{config_data["model"]["repo_id"]}"\n'
    toml_content += f'quantisation = "{config_data["model"]["quantisation"]}"\n'

    try:
        config_path.write_text(toml_content)
        print(f"\nConfiguration written to {config_path}")
    except Exception as e:
        print(f"ERROR: Could not write configuration: {e}")
        return 1

    print("\nSetup complete. Run 'make doctor' to verify all components.")
    return 0


def main() -> None:
    """Entry point for clinicloop-install command."""
    from pathlib import Path

    hardware_tiers_path = (Path(__file__).parent / "hardware_tiers.toml").resolve()
    exit(run_setup(str(hardware_tiers_path)))


if __name__ == "__main__":
    main()
