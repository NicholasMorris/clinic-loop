"""Tests for scanner.scan_tree() and scanner.scan_payload().

AC1: Denylisted names reported with path, line, rule ID (R7).
AC2: I6 words matched case-insensitively and as whole words.
AC6: All four non-source content kinds scanned (cassettes, diagrams, results, payload).
"""

import hashlib
from pathlib import Path

import pytest

from clinicloop.naminglint.scanner import load_denylist, scan_payload, scan_tree


def compute_hashes(name: str) -> set[str]:
    """Compute all n-gram hashes for a normalized name.

    Normalizes with NFKC and lowercases, then forms tokens and n-grams (1-4 tokens),
    and SHA-256 hashes each.

    Args:
        name: The name to hash.

    Returns:
        Set of 64-character lowercase hex SHA-256 hashes.
    """
    import unicodedata

    normalized = unicodedata.normalize("NFKC", name).lower()
    tokens = normalized.split()

    hashes = set()
    # Generate n-grams of length 1 to 4
    for n in range(1, min(5, len(tokens) + 1)):
        for i in range(len(tokens) - n + 1):
            ngram = " ".join(tokens[i : i + n])
            h = hashlib.sha256(ngram.encode("utf-8")).hexdigest()
            hashes.add(h)

    return hashes


@pytest.mark.checklist_id("I6")
@pytest.mark.checklist_id("R7")
def test_denylisted_name_reported_with_path_line_and_rule_id(tmp_path: Path) -> None:
    """AC1: Fixture tree with planted occurrence yields exit 1, path, line, R7.

    Plants "zeta-fixture-clinic" three times in tmp_path tree with a fixture hash file.
    Expects three hits with file path, line number, and rule ID R7.
    """
    # Create fixture name and compute its hashes
    fixture_name = "zeta-fixture-clinic"
    name_hashes = compute_hashes(fixture_name)

    # Create a fixture hash file
    hash_file = tmp_path / "hashes.txt"
    hash_file.write_text("\n".join(sorted(name_hashes)))

    # Plant three occurrences in different files
    file1 = tmp_path / "file1.txt"
    file1.write_text("This mentions zeta-fixture-clinic here\n")

    file2 = tmp_path / "file2.py"
    file2.write_text("# Some code\n# Another mention: zeta-fixture-clinic\n# More code\n")

    file3 = tmp_path / "dir" / "file3.md"
    file3.parent.mkdir(parents=True)
    file3.write_text("Line 1\nLine 2 zeta-fixture-clinic\nLine 3\n")

    # Load denylist (should not raise)
    denylist = load_denylist(hash_file)

    # Read I6 words from the tracked file
    i6_words_path = Path(__file__).parent.parent.parent / "src" / "clinicloop" / "naminglint" / "i6_words.txt"
    i6_words = set(i6_words_path.read_text().strip().split("\n")) if i6_words_path.exists() else set()

    # Scan the tree
    results = scan_tree(tmp_path, denylist, i6_words)

    # Should find 3 hits, all with R7 rule ID
    assert len(results) == 3, f"Expected 3 hits, got {len(results)}: {results}"

    # Check that results contain R7 rule ID
    for file_path, line_num, rule_id in results:
        assert rule_id == "R7", f"Expected R7, got {rule_id}"
        assert int(line_num) > 0, f"Invalid line number: {line_num}"
        # Verify the path is relative to tmp_path or absolute
        assert "file" in str(file_path), f"Path should reference a file: {file_path}"

    # Verify scanning the same tree with no occurrences (empty hash file) yields 0 hits
    empty_hash_file = tmp_path / "empty_hashes.txt"
    empty_hash_file.write_text("")

    # This should handle empty denylist gracefully
    # The implementation should skip empty denylist scanning
    results_empty = scan_tree(tmp_path, set(), i6_words)
    # Should still find I6 words but no R7 hits
    r7_hits = [r for r in results_empty if r[2] == "R7"]
    assert len(r7_hits) == 0, f"Empty denylist should yield no R7 hits, got {r7_hits}"


@pytest.mark.checklist_id("I6")
def test_i6_word_list_matched_case_insensitively(tmp_path: Path) -> None:
    """AC2: I6 words matched case-insensitively and as whole words only.

    Tests that i6_words are matched:
    - Case-insensitively (FRAUD, fraud, Fraud all match)
    - As whole words only (fraudulent does not match fraud)
    """
    # Use i6 words from the tracked file
    i6_words_path = Path(__file__).parent.parent.parent / "src" / "clinicloop" / "naminglint" / "i6_words.txt"
    i6_words_content = i6_words_path.read_text().strip()
    i6_words = set(i6_words_content.split("\n"))

    # Create test files with various cases and combinations
    file1 = tmp_path / "test1.txt"
    file1.write_text("This is FRAUD\nLowercase fraud here\nMixed Fraud case\n")

    file2 = tmp_path / "test2.txt"
    file2.write_text("Word fraudulent should not match\nBut fraud alone should\n")

    # Empty denylist (only checking I6)
    results = scan_tree(tmp_path, set(), i6_words)

    # Find hits in test1.txt (should be 3: FRAUD, fraud, Fraud)
    file1_hits = [r for r in results if "test1.txt" in str(r[0])]
    i6_hits_file1 = [r for r in file1_hits if r[2] == "I6"]
    assert len(i6_hits_file1) == 3, f"Expected 3 I6 hits in test1.txt, got {len(i6_hits_file1)}: {i6_hits_file1}"

    # Find hits in test2.txt (should be 1: just "fraud", not "fraudulent")
    file2_hits = [r for r in results if "test2.txt" in str(r[0])]
    i6_hits_file2 = [r for r in file2_hits if r[2] == "I6"]
    assert len(i6_hits_file2) == 1, f"Expected 1 I6 hit in test2.txt, got {len(i6_hits_file2)}: {i6_hits_file2}"
    # Verify it's on the right line
    assert i6_hits_file2[0][1] == 2, f"Expected hit on line 2, got line {i6_hits_file2[0][1]}"


@pytest.mark.checklist_id("I6")
@pytest.mark.checklist_id("R7")
def test_all_four_non_source_content_kinds_are_scanned(tmp_path: Path) -> None:
    """AC6: Scanner processes tracked files, cassettes, diagrams, results, and payload.

    Plants one hit in each of four content kinds: source file, cassette, diagram, results.
    Also tests payload scanning with a commit message.
    """
    fixture_name = "zeta-fixture-clinic"
    name_hashes = compute_hashes(fixture_name)

    hash_file = tmp_path / "hashes.txt"
    hash_file.write_text("\n".join(sorted(name_hashes)))
    denylist = load_denylist(hash_file)

    i6_words_path = Path(__file__).parent.parent.parent / "src" / "clinicloop" / "naminglint" / "i6_words.txt"
    i6_words = set(i6_words_path.read_text().strip().split("\n"))

    # 1. Plant hit in tracked source file
    source_file = tmp_path / "src" / "code.py"
    source_file.parent.mkdir(parents=True)
    source_file.write_text('message = "zeta-fixture-clinic"\n')

    # 2. Plant hit in cassette file (*.cassette.json or similar)
    cassette_file = tmp_path / "tests" / "cassettes" / "test_api.cassette.json"
    cassette_file.parent.mkdir(parents=True)
    cassette_file.write_text('{"request": "zeta-fixture-clinic", "response": "ok"}\n')

    # 3. Plant hit in diagram file (*.mermaid or similar)
    diagram_file = tmp_path / "docs" / "arch.mermaid"
    diagram_file.parent.mkdir(parents=True)
    diagram_file.write_text("graph LR\n  A[zeta-fixture-clinic] --> B[Process]\n")

    # 4. Plant hit in results file (*.results.json or similar)
    results_file = tmp_path / "evals" / "results" / "eval.results.json"
    results_file.parent.mkdir(parents=True)
    results_file.write_text('{"case": 1, "output": "zeta-fixture-clinic"}\n')

    # Scan tree - should find 4 R7 hits
    tree_results = scan_tree(tmp_path, denylist, i6_words)
    r7_hits = [r for r in tree_results if r[2] == "R7"]
    assert len(r7_hits) == 4, f"Expected 4 R7 hits (one per content kind), got {len(r7_hits)}"

    # Test payload scanning (commit message)
    commit_message = "docs: Update naming lint\n\nMention zeta-fixture-clinic in commit"
    payload_results = scan_payload(commit_message, denylist, i6_words)
    payload_r7_hits = [r for r in payload_results if r[1] == "R7"]
    assert len(payload_r7_hits) == 1, f"Expected 1 R7 hit in payload, got {len(payload_r7_hits)}"

    # Test payload with I6 word
    commit_with_i6 = "fix: Address fraud detection issues"
    payload_i6_results = scan_payload(commit_with_i6, denylist, i6_words)
    payload_i6_hits = [r for r in payload_i6_results if r[1] == "I6"]
    assert len(payload_i6_hits) == 1, f"Expected 1 I6 hit in payload, got {len(payload_i6_hits)}"
