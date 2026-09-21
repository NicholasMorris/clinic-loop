"""Audio codec utilities for the STT spike.

Handles conversion of audio to mu-law encoding at 8000 Hz sample rate,
which simulates telephony-degraded audio common in real clinic consults.
"""

from pathlib import Path


def to_mulaw(input_path: Path, output_path: Path) -> None:
    """Convert audio to mu-law encoded WAV at 8000 Hz sample rate.

    The mu-law codec and 8000 Hz sample rate simulate the degradation
    typical of telephony-transported audio.

    Args:
        input_path: Path to input audio file.
        output_path: Path to write mu-law output.

    Raises:
        FileNotFoundError: If input file does not exist.
        RuntimeError: If ffmpeg invocation fails.
    """
    raise NotImplementedError
