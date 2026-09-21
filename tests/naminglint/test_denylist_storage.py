"""Tests for denylist storage and loading.

AC3: Running lint over tracked tree yields zero R7 hits and zero I6 hits outside i6_words.txt.
AC4: load_denylist() exits 2 when missing/empty; plaintext tests skip when not provisioned.
"""

import os
from pathlib import Path

import pytest

from clinicloop.naminglint.scanner import load_denylist, scan_tree


@pytest.mark.checklist_id("I6")
@pytest.mark.checklist_id("R7")
def test_tracked_tree_holds_no_hashed_names_and_one_i6_word_file() -> None:
    """AC3: Scan entire tracked tree; expect zero R7 and zero I6 outside i6_words.txt.

    This test runs the scanner over the entire repository and verifies that:
    - No forbidden names are present (zero R7 hits)
    - I6 words appear only in the single tracked file (src/clinicloop/naminglint/i6_words.txt)
    """
    repo_root = Path(__file__).parent.parent.parent

    # Load the actual denylist
    hash_file = repo_root / "src" / "clinicloop" / "naminglint" / "denylist_hashes.txt"
    assert hash_file.exists(), f"Denylist hash file not found at {hash_file}"

    denylist = load_denylist(hash_file)

    # Load I6 words from tracked file
    i6_words_file = repo_root / "src" / "clinicloop" / "naminglint" / "i6_words.txt"
    assert i6_words_file.exists(), f"I6 words file not found at {i6_words_file}"
    i6_words = set(i6_words_file.read_text().strip().split("\n"))

    # Scan the entire repo
    results = scan_tree(repo_root, denylist, i6_words)

    # Check for R7 violations (hashed names)
    r7_hits = [r for r in results if r[2] == "R7"]
    assert len(r7_hits) == 0, f"Found {len(r7_hits)} R7 violations (forbidden names): {r7_hits}"

    # Check for I6 violations (should only appear in i6_words.txt)
    i6_hits = [r for r in results if r[2] == "I6"]
    i6_outside_file = [r for r in i6_hits if "i6_words.txt" not in str(r[0])]
    assert (
        len(i6_outside_file) == 0
    ), f"Found {len(i6_outside_file)} I6 words outside i6_words.txt: {i6_outside_file}"


@pytest.mark.checklist_id("I6")
@pytest.mark.checklist_id("R7")
def test_empty_or_missing_hash_file_exits_two_and_plaintext_tests_skip() -> None:
    """AC4: load_denylist() exits 2 on missing/empty file; plaintext tests skip when not provisioned.

    Tests:
    - load_denylist() raises SystemExit with code 2 when hash file is missing
    - load_denylist() raises SystemExit with code 2 when hash file exists but is empty
    - Tests requiring plaintext denylist skip with reason when CLINICLOOP_NAMING_DENYLIST not set
    """
    # Test 1: Missing hash file
    missing_file = Path("/tmp/nonexistent_denylist_hash_file_12345.txt")
    assert not missing_file.exists()

    with pytest.raises(SystemExit) as exc_info:
        load_denylist(missing_file)
    assert exc_info.value.code == 2, f"Expected exit code 2 for missing file, got {exc_info.value.code}"

    # Test 2: Empty hash file
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        empty_hash_file = Path(f.name)
        f.write("")  # Write nothing

    try:
        with pytest.raises(SystemExit) as exc_info:
            load_denylist(empty_hash_file)
        assert exc_info.value.code == 2, f"Expected exit code 2 for empty file, got {exc_info.value.code}"
    finally:
        empty_hash_file.unlink()

    # Test 3: Tests skip when plaintext source not provisioned
    # The plaintext denylist should be at $XDG_CONFIG_HOME/clinicloop/naming-denylist.txt
    # or at path given by CLINICLOOP_NAMING_DENYLIST environment variable
    plaintext_path = os.getenv("CLINICLOOP_NAMING_DENYLIST")
    if not plaintext_path:
        # Try default location
        xdg_config = os.getenv("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
        plaintext_path = os.path.join(xdg_config, "clinicloop", "naming-denylist.txt")

    plaintext_file = Path(plaintext_path)
    if not plaintext_file.exists():
        # Tests that require plaintext should skip
        pytest.skip("plaintext denylist not provisioned")
