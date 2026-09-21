"""Spike report schema for text-to-speech measurement."""

from pydantic import BaseModel, Field, field_validator


class SpikeReport(BaseModel):
    """Measured fields from the text-to-speech spike run.

    These measurements drive the branching decision for audio generation strategy.
    """

    real_time_factor: float = Field(
        ..., description="Real-time factor for TTS processing"
    )
    peak_rss_bytes: int = Field(..., description="Peak RSS memory in bytes")
    disclaimer_offset_s: float = Field(..., description="Disclaimer offset in seconds")
    disclaimer_duration_s: float = Field(..., description="Disclaimer duration in seconds")
    disclaimer_occurrences_per_generation: int = Field(
        ..., description="Number of disclaimer occurrences per generation"
    )
    disclaimer_excludable: bool = Field(
        ..., description="Whether the disclaimer can be excluded"
    )
    three_minute_render_seconds: float = Field(
        ..., description="Time to render a 3-minute consult in seconds"
    )
    corpus_size: int = Field(..., description="Size of the audio corpus")
    per_turn_samples: int = Field(..., description="Number of samples per turn")
    measured_sample_duration_s: float = Field(
        ..., description="Duration of measured samples in seconds"
    )


class ManifestEntry(BaseModel):
    """Entry in the spike audio manifest.

    All spike audio must be marked as synthetic and include a SHA-256 hash.
    """

    clip_id: str = Field(..., description="Unique clip identifier")
    path: str = Field(..., description="Path to the audio file")
    sha256: str = Field(..., description="SHA-256 hash of the audio file")
    speaker_count: int = Field(..., description="Number of speakers in the clip")
    duration_s: float = Field(..., description="Duration of the clip in seconds")
    is_synthetic: bool = Field(
        ...,
        description="Must be True; spike clips are synthetic only",
    )
    produced_by: str = Field(..., description="Name of the worker that produced the clip")

    @field_validator("is_synthetic")
    @classmethod
    def validate_is_synthetic(cls, v: bool) -> bool:
        """Spike audio must be marked as synthetic."""
        if not v:
            raise ValueError("is_synthetic must be True; spike audio is synthetic only")
        return v


class SampleManifest(BaseModel):
    """Manifest of spike audio samples.

    This provides interim provenance control until M4-2 ledger and allowlist are built.
    """

    entries: list[ManifestEntry] = Field(default_factory=list)

    def add_entry(self, entry: ManifestEntry) -> None:
        """Add a manifest entry."""
        self.entries.append(entry)
