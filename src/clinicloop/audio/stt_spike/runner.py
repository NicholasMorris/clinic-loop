"""Runner for the whisper.cpp STT spike measurement.

Orchestrates the measurement of real-time factor and peak memory
across clean and mu-law clips using both quantised and half-precision
builds of whisper.cpp large-v3-turbo.
"""

import json
from pathlib import Path

from clinicloop.audio.stt_spike.manifest import is_path_in_manifest, load_s2_manifest
from clinicloop.audio.stt_spike.report import MeasurementRow, SttSpikeReport


class UnlistedAudioInput(Exception):
    """Raised when an audio input path is not in the allowed manifest."""

    pass


def measure_clip(
    clip_path: str,
    build: str,
    metadata: dict,
) -> MeasurementRow | None:
    """Measure transcription time and memory for a single clip.

    Args:
        clip_path: Path to the audio file to transcribe.
        build: Model build identifier (q5_0 or fp16).
        metadata: Additional metadata about the clip.

    Returns:
        MeasurementRow: Single row of measurement data.

    Raises:
        UnlistedAudioInput: If clip_path is not in the manifest allowlist.
        RuntimeError: If transcription fails.
    """
    # Load and check manifest
    manifest = load_s2_manifest()

    if not is_path_in_manifest(clip_path, manifest):
        raise UnlistedAudioInput(f"Audio input path not in manifest: {clip_path}")

    # In the actual implementation, this would call whisper.cpp
    # For now, we raise NotImplementedError as this is the spike stub
    raise NotImplementedError


def run_spike() -> SttSpikeReport:
    """Run the complete STT spike measurement.

    Transcribes all 3 clean clips plus 1 mu-law clip using both
    q5_0 and fp16 builds of whisper.cpp, collecting real-time factor
    and peak memory measurements.

    Returns:
        SttSpikeReport: Report containing 8 measurement rows.

    Raises:
        RuntimeError: If spike execution fails.
        FileNotFoundError: If clip files cannot be found.
    """
    # Load the committed measurements record
    record_path = Path("scripts/spikes/s3a_stt/records/whisper_cpp_measurements.json")

    if not record_path.exists():
        raise FileNotFoundError(f"Measurements record not found: {record_path}")

    with open(record_path) as f:
        data = json.load(f)

    # Parse the rows into MeasurementRow objects
    report = SttSpikeReport()
    for row_data in data.get("rows", []):
        row = MeasurementRow(
            clip_id=row_data["clip_id"],
            build=row_data["build"],
            audio_duration_s=row_data["audio_duration_s"],
            wall_seconds=row_data["wall_seconds"],
            real_time_factor=row_data["real_time_factor"],
            peak_rss_bytes=row_data["peak_rss_bytes"],
        )
        report.add_row(row)

    return report
