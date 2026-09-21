"""CLI entry point for naming lint.

This module provides the command-line interface for the naming lint scanner.
It can be invoked by the pre-commit hook or manually for scanning the repository.

Usage:
    python -m clinicloop.naminglint.lint [--tree | --payload FILE]

    --tree        Scan the entire tracked tree (default)
    --payload FILE   Scan a payload file (commit message, PR text, etc.)

Exit codes:
    0: No violations found
    1: Violations found
    2: Configuration error (missing/empty denylist)
"""

import argparse
import sys
from pathlib import Path

from clinicloop.naminglint.scanner import load_denylist, scan_payload, scan_tree


def get_repo_root() -> Path:
    """Get the repository root by looking for .git directory.

    Returns:
        Path to the repository root.

    Raises:
        SystemExit: If no .git directory is found.
    """
    current = Path.cwd()
    for parent in [current, *current.parents]:
        if (parent / ".git").exists():
            return parent

    print("error: Not in a git repository", file=sys.stderr)
    sys.exit(2)


def load_i6_words(repo_root: Path) -> set[str]:
    """Load I6 words from the tracked file.

    Args:
        repo_root: Repository root path.

    Returns:
        Set of I6 words.

    Raises:
        SystemExit: If the I6 words file is not found.
    """
    i6_words_file = repo_root / "src" / "clinicloop" / "naminglint" / "i6_words.txt"
    if not i6_words_file.exists():
        print(f"error: I6 words file not found at {i6_words_file}", file=sys.stderr)
        sys.exit(2)

    return set(i6_words_file.read_text().strip().split("\n"))


def report_results(
    results: list[tuple] | list[tuple[str, int, str]],  # type: ignore[type-arg]
    payload_mode: bool,
) -> int:
    """Report lint results and return exit code.

    Args:
        results: List of tuples. For tree: (file_path, line_num, rule_id).
                 For payload: (line_num, rule_id).
        payload_mode: True if scanning a payload, False if scanning tree.

    Returns:
        Exit code (0 if no violations, 1 if violations found).
    """
    if not results:
        return 0

    # Group by type for reporting
    r7_hits = [r for r in results if r[-2] == "R7" or (payload_mode and r[1] == "R7")]
    i6_hits = [r for r in results if r[-2] == "I6" or (payload_mode and r[1] == "I6")]

    # Report violations
    print(f"error: Naming lint found {len(results)} violation(s):", file=sys.stderr)

    if r7_hits:
        print(f"  R7 (forbidden names): {len(r7_hits)} hit(s)", file=sys.stderr)
        for hit in r7_hits[:5]:
            if payload_mode:
                print(f"    line {hit[0]}: {hit[1]}", file=sys.stderr)
            else:
                print(f"    {hit[0]}:{hit[1]}: {hit[2]}", file=sys.stderr)
        if len(r7_hits) > 5:
            print(f"    ... and {len(r7_hits) - 5} more", file=sys.stderr)

    if i6_hits:
        print(f"  I6 (forbidden words): {len(i6_hits)} hit(s)", file=sys.stderr)
        for hit in i6_hits[:5]:
            if payload_mode:
                print(f"    line {hit[0]}: {hit[1]}", file=sys.stderr)
            else:
                print(f"    {hit[0]}:{hit[1]}: {hit[2]}", file=sys.stderr)
        if len(i6_hits) > 5:
            print(f"    ... and {len(i6_hits) - 5} more", file=sys.stderr)

    return 1


def main() -> None:
    """Main entry point for naming lint CLI."""
    parser = argparse.ArgumentParser(description="Naming lint: detect forbidden names and I6 words")
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--tree",
        action="store_true",
        default=True,
        help="Scan the entire tracked tree (default)",
    )
    group.add_argument(
        "--payload",
        type=str,
        help="Scan a payload file (commit message, PR text, etc.)",
    )

    args = parser.parse_args()

    repo_root = get_repo_root()

    # Load denylist and I6 words
    hash_file = repo_root / "src" / "clinicloop" / "naminglint" / "denylist_hashes.txt"
    denylist = load_denylist(hash_file)
    i6_words = load_i6_words(repo_root)

    # Scan and report
    if args.payload:
        # Scan payload file
        try:
            content = Path(args.payload).read_text()
        except (OSError, UnicodeDecodeError) as e:
            print(f"error: Failed to read payload file: {e}", file=sys.stderr)
            sys.exit(2)

        payload_results = scan_payload(content, denylist, i6_words)
        exit_code = report_results(payload_results, payload_mode=True)
    else:
        # Scan tree
        tree_results = scan_tree(repo_root, denylist, i6_words)
        exit_code = report_results(tree_results, payload_mode=False)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
