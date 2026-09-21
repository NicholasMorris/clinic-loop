"""Audio codec utilities for the STT spike.

Handles conversion of audio to mu-law encoding at 8000 Hz sample rate,
which simulates telephony-degraded audio common in real clinic consults.
"""

import subprocess
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
    input_path = Path(input_path)
    output_path = Path(output_path)

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    # Use ffmpeg to convert to mu-law at 8000 Hz
    cmd = [
        "ffmpeg",
        "-i",
        str(input_path),
        "-acodec",
        "pcm_mulaw",
        "-ar",
        "8000",
        "-y",  # Overwrite output file
        str(output_path),
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg conversion failed for {input_path}: {result.stderr}")
