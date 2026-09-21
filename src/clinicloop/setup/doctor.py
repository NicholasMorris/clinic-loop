"""System configuration checker (doctor command)."""

import shutil
import subprocess
import tomllib
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


def get_binary_version(binary_path: str) -> str:
    """Get version string from a binary.

    Args:
        binary_path: Full path to the binary.

    Returns:
        Version string.
    """
    try:
        result = subprocess.run(
            [binary_path, "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip().split("\n")[0]
        # Fallback for some binaries that use -version
        result = subprocess.run(
            [binary_path, "-version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip().split("\n")[0]
    except Exception:
        pass

    return "unknown"


def run_doctor(
    hardware_tiers_path: str,
    config_path: Path | None = None,
) -> int:
    """Check system configuration and report status.

    Args:
        hardware_tiers_path: Path to hardware_tiers.toml.
        config_path: Optional path to models.toml config file to read.

    Returns:
        Exit code: 0 if all checks pass, 1 if any checks fail.
    """
    exit_code = 0
    missing_components = []

    # Detect system memory
    try:
        memory_gib = get_available_memory_gib()
        print(f"System Memory: {memory_gib} GiB")
    except RuntimeError as e:
        print(f"ERROR: Could not detect system memory: {e}")
        return 1

    # Load tiers and resolve
    try:
        tiers_path = Path(hardware_tiers_path)
        tiers = load_tiers(tiers_path)
        selected_tier = resolve_tier(tiers)
        print(f"Hardware Tier: {selected_tier['label']}")
        print(f"LLM Model: {selected_tier['repo_id']}")
        print(f"Quantisation: {selected_tier['quantisation']}")
    except Exception as e:
        print(f"ERROR: Could not load hardware tiers: {e}")
        return 1

    # Check ffmpeg
    ffmpeg_path = find_binary("ffmpeg")
    if ffmpeg_path:
        version = get_binary_version(ffmpeg_path)
        print(f"ffmpeg: {ffmpeg_path} ({version})")
    else:
        print("ERROR: ffmpeg not found")
        missing_components.append("ffmpeg")
        exit_code = 1

    # Check whisper.cpp
    whisper_path = find_binary("whisper.cpp")
    if whisper_path:
        version = get_binary_version(whisper_path)
        print(f"whisper.cpp: {whisper_path} ({version})")
    else:
        print("ERROR: whisper.cpp not found")
        missing_components.append("whisper.cpp")
        exit_code = 1

    # Read config if provided
    if config_path and config_path.exists():
        try:
            with open(config_path, "rb") as f:
                config = tomllib.load(f)
                if "model" in config:
                    model_config = config["model"]
                    print(f"Config File: {config_path}")
                    if "tier" in model_config:
                        print(f"Configured Tier: {model_config['tier']}")
                    if "repo_id" in model_config:
                        print(f"Configured Model: {model_config['repo_id']}")
                    if "quantisation" in model_config:
                        print(f"Configured Quantisation: {model_config['quantisation']}")
        except Exception as e:
            print(f"Warning: Could not read config file: {e}")

    return exit_code


def main() -> None:
    """Entry point for clinicloop-doctor command."""
    from pathlib import Path

    hardware_tiers_path = (Path(__file__).parent / "hardware_tiers.toml").resolve()
    exit(run_doctor(str(hardware_tiers_path)))


if __name__ == "__main__":
    main()
