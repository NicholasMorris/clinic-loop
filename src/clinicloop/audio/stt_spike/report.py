"""Spike report schema for whisper.cpp speech-to-text measurement."""

from pydantic import BaseModel, Field


class MeasurementRow(BaseModel):
    """Single measurement row from the STT spike.

    Each row records the real-time factor and peak memory for one clip
    on one build (q5_0 or fp16).
    """

    clip_id: str = Field(..., description="Unique clip identifier")
    build: str = Field(..., description="Model build (q5_0 or fp16)")
    audio_duration_s: float = Field(..., description="Duration of the audio clip in seconds")
    wall_seconds: float = Field(..., description="Wall clock time to transcribe in seconds")
    real_time_factor: float = Field(
        ..., description="Real-time factor (wall_seconds / audio_duration_s)"
    )
    peak_rss_bytes: int = Field(
        ..., description="Peak resident set size in bytes during transcription"
    )


class SttSpikeReport(BaseModel):
    """Committed report of STT spike measurements.

    Contains exactly 8 measurement rows: 3 clean clips + 1 mu-law clip,
    each measured on both q5_0 and fp16 builds.
    """

    rows: list[MeasurementRow] = Field(default_factory=list)

    def add_row(self, row: MeasurementRow) -> None:
        """Add a measurement row to the report.

        Args:
            row: MeasurementRow to add.
        """
        self.rows.append(row)
