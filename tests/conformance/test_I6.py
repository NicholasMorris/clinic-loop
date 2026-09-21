"""I6 conformance test: Naming lint detects I6 words.

Runs the naming lint over the entire tracked tree and fails if I6 words are found
outside of designated exempt paths.
"""

from pathlib import Path

import pytest

from clinicloop.naminglint.scanner import load_denylist, scan_tree


@pytest.mark.checklist_id("I6")
def test_i6_no_forbidden_words_in_tree() -> None:
    """I6: Naming lint finds no forbidden I6 words in tracked tree (outside exempts).

    Scans every tracked file and returns non-zero if I6 words appear outside:
    - src/clinicloop/naminglint/i6_words.txt (the single tracked word list)
    - tests/naminglint/ (test files)
    - tests/compliance/data/ (test data)
    """
    repo_root = Path(__file__).parent.parent.parent

    # Load denylist
    hash_file = repo_root / "src" / "clinicloop" / "naminglint" / "denylist_hashes.txt"
    if not hash_file.exists():
        pytest.skip("Denylist hash file not found")

    denylist = load_denylist(hash_file)

    # Load I6 words from tracked file
    i6_words_file = repo_root / "src" / "clinicloop" / "naminglint" / "i6_words.txt"
    if not i6_words_file.exists():
        pytest.skip("I6 words file not found")

    i6_words = set(i6_words_file.read_text().strip().split("\n"))

    # Scan the entire repo
    results = scan_tree(repo_root, denylist, i6_words)

    # Filter for I6 hits
    i6_hits = [r for r in results if r[2] == "I6"]
    i6_outside_file = [r for r in i6_hits if "i6_words.txt" not in str(r[0])]

    # Report results
    if i6_outside_file:
        hit_summary = "\n  ".join(
            f"{hit[0]}:{hit[1]} - {hit[2]}" for hit in i6_outside_file[:10]
        )
        pytest.fail(
            f"Found {len(i6_outside_file)} I6 word violations outside exempt paths:\n  {hit_summary}"
        )
