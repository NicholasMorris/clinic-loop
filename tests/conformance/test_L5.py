"""Conformance test for L5: Audio pipeline (TTS/STT).

L5 requires measured text-to-speech (TTS) and speech-to-text (STT) performance
on this machine, with real numbers from S2 and S3 spikes recorded in documentation.
"""

import json
from pathlib import Path

import pytest

from clinicloop.audio.spike.branch import select_branch
from clinicloop.audio.spike.report import SpikeReport


class TestL5AudioTTSMeasured:
    """L5: TTS performance measured and documented."""

    def test_tts_spike_report_exists_and_validates(self) -> None:
        """TTS spike report is committed and validates as SpikeReport."""
        report_path = Path(__file__).parent.parent.parent / "scripts" / "spikes" / "s2_tts" / "report.json"
        assert report_path.exists(), "scripts/spikes/s2_tts/report.json must exist"

        with open(report_path) as f:
            report_data = json.load(f)

        report = SpikeReport(**report_data)

        # All fields present and non-null
        assert report.real_time_factor > 0
        assert report.peak_rss_bytes > 0
        assert report.disclaimer_offset_s >= 0.0
        assert report.disclaimer_duration_s >= 0.0
        assert report.disclaimer_occurrences_per_generation >= 0
        assert report.three_minute_render_seconds > 0
        assert report.corpus_size > 0
        assert report.per_turn_samples > 0
        assert report.measured_sample_duration_s > 0

    def test_tts_spike_branch_documented(self) -> None:
        """TTS spike documents the selected branch."""
        docs_path = Path(__file__).parent.parent.parent / "docs" / "audio" / "tts-spike.md"
        assert docs_path.exists(), "docs/audio/tts-spike.md must exist"

        docs_content = docs_path.read_text()

        # Extract branch from docs
        import re
        match = re.search(r"[Bb]ranch\s+([ABC])", docs_content)
        assert match, "Branch letter must be documented in tts-spike.md"
        documented_branch = match.group(1)
        assert documented_branch in ["A", "B", "C"]

    def test_tts_spike_docs_match_report(self) -> None:
        """TTS spike documentation references match the committed report."""
        report_path = Path(__file__).parent.parent.parent / "scripts" / "spikes" / "s2_tts" / "report.json"
        docs_path = Path(__file__).parent.parent.parent / "docs" / "audio" / "tts-spike.md"

        with open(report_path) as f:
            report = SpikeReport(**json.load(f))

        docs_content = docs_path.read_text()

        # Branch must match the rule
        import re
        match = re.search(r"[Bb]ranch\s+([ABC])", docs_content)
        assert match
        documented_branch = match.group(1)
        assert documented_branch == select_branch(report)

    def test_tts_engine_adr_exists_and_is_accepted(self) -> None:
        """TTS engine ADR exists and has Accepted status."""
        adr_path = Path(__file__).parent.parent.parent / "docs" / "adr" / "tts-engine-and-pin.md"
        assert adr_path.exists(), "docs/adr/tts-engine-and-pin.md must exist"

        content = adr_path.read_text()
        assert "Accepted" in content, "ADR must have status Accepted"
        assert "VibeVoice" in content or "vibevoice" in content, "ADR must name the TTS engine"

    def test_tts_version_pins_recorded(self) -> None:
        """TTS version pins are recorded in pins.toml."""
        pins_path = Path(__file__).parent.parent.parent / "scripts" / "spikes" / "s2_tts" / "pins.toml"
        assert pins_path.exists(), "scripts/spikes/s2_tts/pins.toml must exist"

        import tomllib
        with open(pins_path, "rb") as f:
            pins_data = tomllib.load(f)

        pins = pins_data.get("pins", {})
        # Check for version pins
        assert "transformers_version" in pins or "fork_commit" in pins, "Version info must be recorded"
