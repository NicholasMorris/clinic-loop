"""R7 conformance test: Naming lint detects forbidden hashed names.

Runs the naming lint over the entire tracked tree and fails if any forbidden names
from the denylist are found.
"""

from pathlib import Path

import pytest

from clinicloop.naminglint.scanner import load_denylist, scan_tree


@pytest.mark.checklist_id("R7")
def test_r7_no_forbidden_names_in_tree() -> None:
    """R7: Naming lint finds no forbidden names in tracked tree.

    Runs the scanner over every tracked file with the denylist as input.
    Fails if any R7 violations are found. The denylist is stored as hashes
    to avoid committing the forbidden names.
    """
    repo_root = Path(__file__).parent.parent.parent

    # Load denylist
    hash_file = repo_root / "src" / "clinicloop" / "naminglint" / "denylist_hashes.txt"
    if not hash_file.exists():
        pytest.skip("Denylist hash file not found")

    denylist = load_denylist(hash_file)

    # Load I6 words for complete scan
    i6_words_file = repo_root / "src" / "clinicloop" / "naminglint" / "i6_words.txt"
    if not i6_words_file.exists():
        pytest.skip("I6 words file not found")

    i6_words = set(i6_words_file.read_text().strip().split("\n"))

    # Scan the entire repo
    results = scan_tree(repo_root, denylist, i6_words)

    # Filter for R7 violations
    r7_hits = [r for r in results if r[2] == "R7"]

    # Report results
    if r7_hits:
        hit_summary = "\n  ".join(f"{hit[0]}:{hit[1]} - {hit[2]}" for hit in r7_hits[:10])
        pytest.fail(f"Found {len(r7_hits)} R7 violations (forbidden names):\n  {hit_summary}")
