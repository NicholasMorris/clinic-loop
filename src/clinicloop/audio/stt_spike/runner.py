"""Runner for the whisper.cpp STT spike measurement.

Orchestrates the measurement of real-time factor and peak memory
across clean and mu-law clips using both quantised and half-precision
builds of whisper.cpp large-v3-turbo.
"""

from pathlib import Path

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
    raise NotImplementedError
