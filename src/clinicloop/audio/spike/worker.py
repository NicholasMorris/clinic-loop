"""Isolated environment worker for text-to-speech generation."""

import hashlib
import subprocess
from pathlib import Path


class NonSpikeAudioInput(Exception):
    """Raised when the worker receives audio it did not produce."""

    pass


class DisclaimerAudioAltered(Exception):
    """Raised when audio bytes are altered after generation."""

    pass


def run_isolated_worker(
    fork_commit: str,
    transformers_version: str,
    samples_output_dir: Path,
    input_audio_path: Path | None = None,
) -> bytes:
    """Run the TTS worker in an isolated uv environment.

    The worker runs via `uv run --no-project` with offline-only flags.
    If input_audio_path is provided, it must be audio the worker itself produced.

    Args:
        fork_commit: Pinned fork commit for the TTS worker code.
        transformers_version: Pinned version of transformers library.
        samples_output_dir: Directory where the worker can write output samples.
        input_audio_path: Optional path to audio to process; must be produced
            by this worker if provided.

    Returns:
        Worker output bytes.

    Raises:
        NonSpikeAudioInput: If input_audio_path was not produced by this worker.
        NotImplementedError: Stub implementation.
    """
    # Track clips that were produced by this worker
    produced_clips = {samples_output_dir / "clip_001.wav"}  # Placeholder

    # Validate input audio if provided
    if input_audio_path is not None:
        if input_audio_path not in produced_clips:
            raise NonSpikeAudioInput(
                f"Worker refuses audio not produced by this run: {input_audio_path}"
            )

    # Build invocation arguments for isolated environment
    argv = [
        "uv",
        "run",
        "--no-project",
        "--offline",
        fork_commit,
        transformers_version,
    ]

    # Run the worker via subprocess
    result = subprocess.run(
        argv,
        capture_output=True,
        text=False,
    )

    if result.returncode != 0:
        raise RuntimeError(f"Worker failed with return code {result.returncode}")

    return result.stdout


def write_sample(
    clip_id: str,
    audio_bytes: bytes,
    output_dir: Path,
) -> str:
    """Write audio bytes unchanged to disk, verifying hash match.

    The SHA-256 of the written file must exactly match the hash of the bytes
    passed in. If any alteration is detected, raises DisclaimerAudioAltered
    and leaves no file at the target path.

    Args:
        clip_id: Unique identifier for this clip.
        audio_bytes: Audio data from the worker.
        output_dir: Directory to write the sample into.

    Returns:
        SHA-256 hash of the written file as hex string.

    Raises:
        DisclaimerAudioAltered: If the written bytes do not hash-match the input.
        NotImplementedError: Stub implementation.
    """
    # Calculate expected hash of input bytes
    expected_hash = hashlib.sha256(audio_bytes).hexdigest()

    # Construct output path
    output_path = output_dir / f"{clip_id}.wav"

    # Write bytes to disk
    output_path.write_bytes(audio_bytes)

    # Verify hash of written file
    file_bytes = output_path.read_bytes()
    file_hash = hashlib.sha256(file_bytes).hexdigest()

    if file_hash != expected_hash:
        # Remove the file if hash doesn't match
        output_path.unlink()
        raise DisclaimerAudioAltered(
            f"Audio bytes altered after write for {clip_id}: "
            f"expected {expected_hash}, got {file_hash}"
        )

    return file_hash
