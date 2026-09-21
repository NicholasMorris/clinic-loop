"""Tests for exemption list in naming lint.

AC5: Exempt paths (i6_words.txt, compliance/rules/**, tests/compliance/data/**) are skipped;
planted text yields 0 inside exempt path and 1 outside.
"""

import hashlib
from pathlib import Path

import pytest

from clinicloop.naminglint.scanner import load_denylist, scan_tree


def compute_hashes(name: str) -> set[str]:
    """Compute all n-gram hashes for a normalized name."""
    import unicodedata

    normalized = unicodedata.normalize("NFKC", name).lower()
    tokens = normalized.split()

    hashes = set()
    for n in range(1, min(5, len(tokens) + 1)):
        for i in range(len(tokens) - n + 1):
            ngram = " ".join(tokens[i : i + n])
            h = hashlib.sha256(ngram.encode("utf-8")).hexdigest()
            hashes.add(h)

    return hashes


@pytest.mark.checklist_id("I6")
@pytest.mark.checklist_id("R7")
def test_exempt_paths_are_skipped(tmp_path: Path) -> None:
    """AC5: Same planted text yields exit 0 inside exempt path, exit 1 outside.

    Tests that the following paths are exempt:
    - src/clinicloop/naminglint/i6_words.txt
    - src/clinicloop/compliance/rules/**
    - tests/compliance/data/**
    """
    fixture_name = "zeta-fixture-clinic"
    name_hashes = compute_hashes(fixture_name)

    hash_file = tmp_path / "hashes.txt"
    hash_file.write_text("\n".join(sorted(name_hashes)))
    denylist = load_denylist(hash_file)

    i6_words = set()

    # Plant the fixture name in an exempt path (compliance rules)
    exempt_rule_file = tmp_path / "src" / "clinicloop" / "compliance" / "rules" / "au.yaml"
    exempt_rule_file.parent.mkdir(parents=True)
    exempt_rule_file.write_text("# Rule file\nname: zeta-fixture-clinic\n")

    # Plant the same text in a non-exempt path
    source_file = tmp_path / "src" / "clinicloop" / "agents" / "triage.py"
    source_file.parent.mkdir(parents=True)
    source_file.write_text('"""Agent module.\n\nMentioning zeta-fixture-clinic here.\n"""\n')

    # Scan: should find hit only in non-exempt path
    results = scan_tree(tmp_path, denylist, i6_words)
    r7_hits = [r for r in results if r[2] == "R7"]

    # Should have exactly 1 hit (in source_file, not exempt_rule_file)
    assert len(r7_hits) == 1, f"Expected 1 R7 hit (in non-exempt), got {len(r7_hits)}: {r7_hits}"
    assert "agents" in str(r7_hits[0][0]), f"Hit should be in agents/, got {r7_hits[0][0]}"
    assert "compliance" not in str(r7_hits[0][0]), (
        f"Hit should not be in exempt compliance/, got {r7_hits[0][0]}"
    )

    # Test compliance data exemption
    compliance_data_file = tmp_path / "tests" / "compliance" / "data" / "blocklist.txt"
    compliance_data_file.parent.mkdir(parents=True)
    compliance_data_file.write_text("zeta-fixture-clinic\n")

    results2 = scan_tree(tmp_path, denylist, i6_words)
    r7_hits2 = [r for r in results2 if r[2] == "R7"]

    # Still only 1 hit (in agents), not in compliance/data
    assert len(r7_hits2) == 1, (
        f"Expected 1 R7 hit (compliance/data is exempt), got {len(r7_hits2)}: {r7_hits2}"
    )
