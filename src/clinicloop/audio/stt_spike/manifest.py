"""Load and validate the S2 sample manifest for spike clips.

The manifest provides interim provenance control for spike clips,
listing which audio files are allowed for use in the measurement.
"""

import json
from pathlib import Path

from clinicloop.audio.spike.report import SampleManifest


def load_s2_manifest() -> SampleManifest:
    """Load the S2 sample manifest from the standard location.

    Returns:
        SampleManifest: Manifest containing allowed spike clip entries.

    Raises:
        FileNotFoundError: If the manifest file is not found.
    """
    manifest_path = Path("scripts/spikes/s2_tts/samples/manifest.json")

    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found at {manifest_path}")

    with open(manifest_path) as f:
        data = json.load(f)

    manifest = SampleManifest(**data)
    return manifest
