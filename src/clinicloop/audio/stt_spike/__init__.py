"""Spike for whisper.cpp speech-to-text measurement.

Measures real-time factor and peak resident memory of the STT model on
clean synthetic clips and mu-law encoded clips using both quantised (q5_0)
and half-precision (fp16) builds.
"""

from clinicloop.audio.stt_spike.runner import UnlistedAudioInput, measure_clip, run_spike

__all__ = ["UnlistedAudioInput", "measure_clip", "run_spike"]
