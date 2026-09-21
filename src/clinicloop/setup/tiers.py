"""Hardware tier detection and resolution."""

import tomllib
from pathlib import Path
from typing import Any


class UnsupportedMemoryTier(Exception):
    """Raised when available memory does not match any supported tier."""

    pass


def get_available_memory_gib() -> int:
    """Detect available system memory in GiB.

    Returns:
        Available memory in GiB.
    """
    try:
        import psutil  # type: ignore[import-untyped]

        return int(psutil.virtual_memory().total / (1024**3))
    except ImportError:
        # Fallback: try to read from system on macOS/Linux
        try:
            import subprocess

            if hasattr(subprocess, "run"):
                # Try macOS
                result = subprocess.run(
                    ["sysctl", "-n", "hw.memsize"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    return int(int(result.stdout.strip()) / (1024**3))
        except Exception:
            pass

        # Fallback to reading /proc/meminfo on Linux
        try:
            with open("/proc/meminfo") as f:
                for line in f:
                    if line.startswith("MemTotal:"):
                        kb = int(line.split()[1])
                        return int(kb / (1024**2))
        except FileNotFoundError:
            pass

        raise RuntimeError("Could not detect available memory")


def load_tiers(config_path: Path) -> list[dict[str, Any]]:
    """Load hardware tiers from TOML configuration file.

    Args:
        config_path: Path to hardware_tiers.toml file.

    Returns:
        List of tier dictionaries with keys: label, min_gib, repo_id,
        quantisation, fallback_repo_id, provenance.

    Raises:
        ValueError: If validation fails (e.g., missing required key).
    """
    required_keys = {
        "label",
        "min_gib",
        "repo_id",
        "quantisation",
        "fallback_repo_id",
        "provenance",
    }

    with open(config_path, "rb") as f:
        data = tomllib.load(f)

    if "tier" not in data:
        raise ValueError("No 'tier' section found in hardware_tiers.toml")

    tiers = data["tier"]
    if not isinstance(tiers, list):
        raise ValueError("'tier' must be a list of tables")

    validated_tiers = []
    for tier in tiers:
        # Check all required keys are present
        missing_keys = required_keys - set(tier.keys())
        if missing_keys:
            label = tier.get("label", "<unknown>")
            raise ValueError(
                f"Row '{label}' missing required keys: {', '.join(sorted(missing_keys))}"
            )

        validated_tiers.append(tier)

    return validated_tiers


def resolve_tier(tiers: list[dict[str, Any]]) -> dict[str, Any]:
    """Resolve the appropriate tier based on available memory.

    Args:
        tiers: List of tier dictionaries from load_tiers().

    Returns:
        The selected tier dictionary for the detected memory amount.

    Raises:
        UnsupportedMemoryTier: If available memory is below the lowest tier.
    """
    memory_gib = get_available_memory_gib()

    # Sort by min_gib descending to find the highest tier that fits
    sorted_tiers = sorted(tiers, key=lambda t: t["min_gib"], reverse=True)

    for tier in sorted_tiers:
        if memory_gib >= tier["min_gib"]:
            return tier

    # If no tier matches, raise error with detected memory
    raise UnsupportedMemoryTier(
        f"Available memory {memory_gib} GiB does not match any supported tier "
        f"(minimum supported: {sorted_tiers[-1]['min_gib']} GiB)"
    )
