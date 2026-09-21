"""Text-to-speech spike measurement and report generation.

Derives report.json and samples/manifest.json from the measurement records.
"""

import json
from pathlib import Path


def run_measurement() -> None:
    """Run the measurement spike and generate report and manifest.

    Raises:
        NotImplementedError: When the function body is not yet implemented.
    """
    raise NotImplementedError


def load_committed_report() -> dict:
    """Load the committed spike report from JSON.

    Returns:
        dict: Parsed report dictionary.

    Raises:
        NotImplementedError: When the function body is not yet implemented.
    """
    raise NotImplementedError


def load_committed_manifest() -> dict:
    """Load the committed sample manifest from JSON.

    Returns:
        dict: Parsed manifest dictionary.

    Raises:
        NotImplementedError: When the function body is not yet implemented.
    """
    raise NotImplementedError


def parse_spike_docs() -> tuple[str, dict]:
    """Parse the spike documentation and ADR files.

    Returns:
        tuple[str, dict]: (documented_branch, pins_dict) where documented_branch
            is the single-character branch letter from tts-spike.md and pins_dict
            contains the fork_commit from pins.toml.

    Raises:
        NotImplementedError: When the function body is not yet implemented.
    """
    raise NotImplementedError
