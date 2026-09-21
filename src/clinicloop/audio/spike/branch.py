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

    Decision rules:
    1. If real_time_factor > 3.0 OR three_minute_render_seconds > 600 → Branch C
    2. Else if disclaimer_occurrences_per_generation > 1 AND NOT disclaimer_excludable
       → Branch A
    3. Else → Branch B

    Args:
        report: Measured fields from the spike run.

    Returns:
        One of "A", "B", or "C" indicating the selected branch.
    """
    # Branch C: Performance thresholds exceeded
    if report.real_time_factor > 3.0 or report.three_minute_render_seconds > 600:
        return "C"

    # Branch A: Disclaimer repeats and cannot be excluded
    if (
        report.disclaimer_occurrences_per_generation > 1
        and not report.disclaimer_excludable
    ):
        return "A"

    # Branch B: Default - metrics permit per-turn synthesis
    return "B"
