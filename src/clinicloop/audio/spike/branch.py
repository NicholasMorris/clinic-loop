"""Branching logic for text-to-speech synthesis strategy selection."""

from clinicloop.audio.spike.report import SpikeReport


def select_branch(report: SpikeReport) -> str:
    """Select the audio generation branch based on spike measurements.

    Three branches are available:
    - Branch B (per-turn synthesis): Default when metrics permit; preferred for
      accuracy and ground truth.
    - Branch A (whole-dialogue): When disclaimer repeats and cannot be excluded;
      requires forced alignment (M4-6).
    - Branch C (limited corpus): When real-time factor or render time exceeds
      thresholds; smaller frozen corpus, shorter consults.

    Args:
        report: Measured fields from the spike run.

    Returns:
        One of "A", "B", or "C" indicating the selected branch.
    """
    raise NotImplementedError
