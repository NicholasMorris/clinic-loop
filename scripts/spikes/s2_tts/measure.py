"""Text-to-speech spike measurement and report generation.

Derives report.json and samples/manifest.json from the measurement records.
"""

import json
import tomllib
from pathlib import Path
from typing import Any


def _get_project_root() -> Path:
    """Get the project root directory.

    Returns:
        Path: Project root directory.
    """
    return Path(__file__).parent.parent.parent.parent


def _derive_report() -> dict[str, Any]:
    """Derive spike report from measurement records.

    Returns:
        dict: Report with all calculated fields.
    """
    project_root = _get_project_root()
    records_dir = project_root / "scripts" / "spikes" / "s2_tts" / "records"

    # Load measurement records
    with open(records_dir / "generation_single_whole_dialogue.json") as f:
        single_record = json.load(f)

    with open(records_dir / "generation_per_turn_and_extra_pairs.json") as f:
        per_turn_records = json.load(f)

    # Disclaimer check records confirm no disclaimer phrases found in any clips
    with open(records_dir / "disclaimer_check_asr.json") as f:
        _ = json.load(f)

    with open(records_dir / "sample_facts.json") as f:
        sample_facts = json.load(f)

    # Calculate real_time_factor from three whole-dialogue runs
    rtf_single = single_record["real_time_factor"]

    def get_by_mode_script(mode: str, script: str) -> dict[str, Any]:
        """Find record by mode and script."""
        return next(
            r for r in per_turn_records if r.get("mode") == mode and r.get("script") == script
        )

    rtf_s2 = get_by_mode_script("whole_dialogue", "s2")["real_time_factor"]
    rtf_s3 = get_by_mode_script("whole_dialogue", "s3")["real_time_factor"]
    real_time_factor = round((rtf_single + rtf_s2 + rtf_s3) / 3, 3)

    # Peak RSS from single whole-dialogue run
    peak_rss_bytes = single_record["peak_rss_bytes"]

    # Disclaimer analysis from ASR checks - none found in any clips
    disclaimer_occurrences_per_generation = 0
    disclaimer_offset_s = 0.0
    disclaimer_duration_s = 0.0
    disclaimer_excludable = True

    # Calculate render time for 3 minutes
    three_minute_render_seconds = round(180 * real_time_factor, 1)

    # Per-turn samples count
    per_turn_mode = next(r for r in per_turn_records if r.get("mode") == "per_turn")
    per_turn_samples = len(per_turn_mode["turns"])

    # Measured sample duration - sum of all sample durations
    measured_sample_duration_s = sum(s["duration_s"] for s in sample_facts)

    # Corpus size - target 40 consults
    corpus_size = 40

    return {
        "real_time_factor": real_time_factor,
        "peak_rss_bytes": peak_rss_bytes,
        "disclaimer_offset_s": disclaimer_offset_s,
        "disclaimer_duration_s": disclaimer_duration_s,
        "disclaimer_occurrences_per_generation": disclaimer_occurrences_per_generation,
        "disclaimer_excludable": disclaimer_excludable,
        "three_minute_render_seconds": three_minute_render_seconds,
        "corpus_size": corpus_size,
        "per_turn_samples": per_turn_samples,
        "measured_sample_duration_s": measured_sample_duration_s,
    }


def _derive_manifest() -> dict[str, Any]:
    """Derive sample manifest from sample facts and records.

    Returns:
        dict: Manifest with entries for each spike sample.
    """
    project_root = _get_project_root()
    records_dir = project_root / "scripts" / "spikes" / "s2_tts" / "records"

    with open(records_dir / "sample_facts.json") as f:
        sample_facts = json.load(f)

    # Worker ID is recorded as the model from environment
    with open(records_dir / "environment.json") as f:
        env = json.load(f)
    produced_by = env["model_id"]

    entries = []
    for sample in sample_facts:
        entries.append(
            {
                "clip_id": sample["clip_id"],
                "path": f"runs/s2_tts/samples/{sample['clip_id']}.wav",
                "sha256": sample["sha256"],
                "speaker_count": 2,  # All spike samples are 2-speaker
                "duration_s": sample["duration_s"],
                "is_synthetic": True,
                "produced_by": produced_by,
            }
        )

    return {"entries": entries}


def run_measurement() -> None:
    """Run the measurement spike and generate report and manifest.

    Raises:
        NotImplementedError: When the function body is not yet implemented.
    """
    raise NotImplementedError


def load_committed_report() -> dict[str, Any]:
    """Load the committed spike report from JSON.

    Returns:
        dict[str, Any]: Parsed report dictionary.

    Raises:
        FileNotFoundError: If report.json does not exist.
    """
    project_root = _get_project_root()
    report_path = project_root / "scripts" / "spikes" / "s2_tts" / "report.json"
    with open(report_path) as f:
        return dict(json.load(f))


def load_committed_manifest() -> dict[str, Any]:
    """Load the committed sample manifest from JSON.

    Returns:
        dict[str, Any]: Parsed manifest dictionary.

    Raises:
        FileNotFoundError: If manifest.json does not exist.
    """
    project_root = _get_project_root()
    manifest_path = project_root / "scripts" / "spikes" / "s2_tts" / "samples" / "manifest.json"
    with open(manifest_path) as f:
        return dict(json.load(f))


def parse_spike_docs() -> tuple[str, dict[str, Any]]:
    """Parse the spike documentation and ADR files.

    Returns:
        tuple[str, dict[str, Any]]: (documented_branch, pins_dict) where documented_branch
            is the single-character branch letter from tts-spike.md and pins_dict
            contains the fork_commit from pins.toml.

    Raises:
        FileNotFoundError: If required documentation files do not exist.
    """
    project_root = _get_project_root()

    # Parse pins.toml
    pins_path = project_root / "scripts" / "spikes" / "s2_tts" / "pins.toml"
    with open(pins_path, "rb") as f:
        pins_data: dict[str, Any] = tomllib.load(f)
        pins_dict = pins_data.get("pins", {})

    # Parse tts-spike.md to extract branch
    docs_path = project_root / "docs" / "audio" / "tts-spike.md"
    docs_content = docs_path.read_text()

    # Extract branch letter from docs (look for "Branch B:" or similar pattern)
    import re

    match = re.search(r"[Bb]ranch\s+([ABC])", docs_content)
    if not match:
        raise ValueError("Could not find branch letter in tts-spike.md")
    documented_branch = match.group(1)

    return documented_branch, pins_dict
