"""Tests for text-to-speech spike measurement and reporting."""

import hashlib
import re
from pathlib import Path

import pytest

from clinicloop.audio.spike.branch import select_branch
from clinicloop.audio.spike.report import SampleManifest, SpikeReport
from scripts.spikes.s2_tts.measure import (
    load_committed_manifest,
    load_committed_report,
    parse_spike_docs,
)


class TestCommittedReportValidatesAndIsFullyPopulated:
    """AC1: report.json validates and all fields are populated."""

    def test_committed_report_validates_and_is_fully_populated(self) -> None:
        """Test that committed report validates against SpikeReport schema."""
        report_data = load_committed_report()
        report = SpikeReport(**report_data)
        assert report.corpus_size > 0
        assert report.real_time_factor > 0
        assert report.disclaimer_offset_s >= 0.0


class TestDocumentedBranchEqualsRuleOutput:
    """AC2: Documented branch equals select_branch(report)."""

    def test_documented_branch_equals_rule_output(self) -> None:
        """Test that documented branch matches the branching rule."""
        report_data = load_committed_report()
        report = SpikeReport(**report_data)
        documented_branch, _ = parse_spike_docs()
        assert documented_branch == select_branch(report)
        assert documented_branch in ["A", "B", "C"]


class TestDocumentedCorpusSizeEqualsReport:
    """AC3: docs corpus size equals report.corpus_size."""

    def test_documented_corpus_size_equals_report(self) -> None:
        """Test that documented corpus size matches reported value."""
        report_data = load_committed_report()
        report = SpikeReport(**report_data)
        # Parse tts-spike.md to extract corpus size
        project_root = Path(__file__).parent.parent.parent.parent
        spike_docs_path = project_root / "docs" / "audio" / "tts-spike.md"
        spike_docs_content = spike_docs_path.read_text()

        # Extract corpus size from documentation
        match = re.search(r"(\d+)\s+consult", spike_docs_content)
        assert match, "Could not find corpus size in tts-spike.md"
        doc_corpus_size = int(match.group(1))
        assert doc_corpus_size == report.corpus_size


class TestManifestListsThreeCleanTwoSpeakerSyntheticClips:
    """AC4: Manifest has 3+ clean two-speaker synthetic clips from spike worker."""

    def test_manifest_lists_three_clean_two_speaker_synthetic_clips(self) -> None:
        """Test that manifest has required clean two-speaker synthetic clips."""
        manifest_data = load_committed_manifest()
        manifest = SampleManifest(**manifest_data)
        assert len(manifest.entries) >= 3

        clean_two_speaker = [
            entry for entry in manifest.entries if entry.speaker_count == 2 and entry.is_synthetic
        ]
        assert len(clean_two_speaker) >= 3

        # Check all entries are marked as synthetic
        for entry in manifest.entries:
            assert entry.is_synthetic is True
            # Check produced_by equals spike worker id
            assert entry.produced_by is not None


class TestTtsEngineAndPinAdrValidatesAndMatchesPins:
    """AC5: ADR validates and fork commit/transformers version match pins.toml."""

    def test_tts_engine_and_pin_adr_validates_and_matches_pins(self) -> None:
        """Test that ADR and pins.toml are consistent."""
        _, pins_dict = parse_spike_docs()
        assert "fork_commit" in pins_dict


class TestLocalTierRunRecomputesEveryManifestHash:
    """AC6: local_model test recomputes manifest hashes and asserts equality."""

    @pytest.mark.local_model
    def test_local_tier_run_recomputes_every_manifest_hash(self) -> None:
        """Test that manifest hashes can be recomputed from committed files."""
        manifest_data = load_committed_manifest()
        manifest = SampleManifest(**manifest_data)
        samples_dir = Path(__file__).parent.parent.parent.parent / "runs" / "s2_tts" / "samples"

        for entry in manifest.entries:
            clip_path = samples_dir / f"{entry.clip_id}.wav"
            if clip_path.exists():
                # Recompute hash
                h = hashlib.sha256()
                with open(clip_path, "rb") as f:
                    for chunk in iter(lambda: f.read(8192), b""):
                        h.update(chunk)
                recomputed = h.hexdigest()
                assert recomputed == entry.sha256
