"""Scanner for forbidden names and I6 words in repository content.

This module scans tracked files, commit messages, and other content for:
- Hashed names from the denylist (R7 rule)
- I6 words (fraud, drug seeker, abuse) that should never be used

The denylist is stored as SHA-256 hashes to avoid committing forbidden names.
I6 words live in a single tracked file (i6_words.txt) with deliberate exception.
"""

import hashlib
import subprocess
import sys
import unicodedata
from pathlib import Path
from typing import Set

# Exempt paths that are allowed to contain forbidden names
EXEMPT_PATHS = {
    "src/clinicloop/naminglint/i6_words.txt",
    "src/clinicloop/compliance/rules",
    "tests/compliance/data",
    "tests/naminglint",  # Test files that intentionally contain I6 words
}

# File patterns to scan (tracked files only; special content kinds scanned separately)
# Note: *.cassette.json, *.mermaid, *.results.json scanned separately for non-tracked files
TRACKABLE_PATTERNS = {
    "*.py",
    "*.md",
    "*.yaml",
    "*.yml",
    "*.txt",
}


def _is_exempt(file_path: Path, repo_root: Path) -> bool:
    """Check if a file path is exempt from scanning.

    Args:
        file_path: The path to check.
        repo_root: The repository root for computing relative path.

    Returns:
        True if the path is exempt, False otherwise.
    """
    try:
        rel_path = str(file_path.relative_to(repo_root))
    except ValueError:
        # Path is not relative to repo_root
        return False

    # Check if path matches any exempt pattern
    for exempt in EXEMPT_PATHS:
        if rel_path == exempt or rel_path.startswith(exempt + "/"):
            return True

    return False


def _get_normalized_tokens(line: str) -> list[str]:
    """Normalize a line and split into tokens.

    Applies NFKC normalization and lowercase, then splits on whitespace.

    Args:
        line: The input line.

    Returns:
        List of normalized tokens.
    """
    normalized = unicodedata.normalize("NFKC", line).lower()
    return normalized.split()


def _compute_ngram_hashes(tokens: list[str]) -> set[str]:
    """Compute SHA-256 hashes for all n-grams (1-4 tokens).

    Args:
        tokens: List of normalized tokens.

    Returns:
        Set of lowercase 64-character hex SHA-256 hashes.
    """
    hashes = set()

    # Generate n-grams of length 1 to 4
    for n in range(1, min(5, len(tokens) + 1)):
        for i in range(len(tokens) - n + 1):
            ngram = " ".join(tokens[i : i + n])
            h = hashlib.sha256(ngram.encode("utf-8")).hexdigest()
            hashes.add(h)

    return hashes


def _match_i6_word(tokens: list[str], i6_words: Set[str]) -> bool:
    """Check if any I6 word appears as a whole word in the token list.

    Args:
        tokens: List of normalized tokens from a line.
        i6_words: Set of I6 words to check (normalized).

    Returns:
        True if any I6 word is matched, False otherwise.
    """
    # For single-token I6 words, check direct match
    for token in tokens:
        if token in i6_words:
            return True

    # For multi-token I6 words (e.g., "drug seeker"), check sequences
    for i6_word in i6_words:
        i6_tokens = i6_word.split()
        if len(i6_tokens) > 1:
            # Check if the sequence appears in tokens
            for j in range(len(tokens) - len(i6_tokens) + 1):
                if tokens[j : j + len(i6_tokens)] == i6_tokens:
                    return True

    return False


def load_denylist(hash_file_path: Path) -> Set[str]:
    """Load the set of forbidden name hashes from a file.

    Args:
        hash_file_path: Path to the file containing SHA-256 hashes, one per line.

    Returns:
        Set of lowercase 64-character hash strings.

    Raises:
        SystemExit: If the file is missing or empty (exit code 2).
    """
    if not hash_file_path.exists():
        print(
            f"error: Denylist hash file not found: {hash_file_path}",
            file=sys.stderr,
        )
        sys.exit(2)

    content = hash_file_path.read_text().strip()

    # Check for empty file
    if not content:
        print(
            f"error: Denylist hash file is empty: {hash_file_path}",
            file=sys.stderr,
        )
        sys.exit(2)

    # Parse hashes (skip empty lines and comments)
    hashes = set()
    for line in content.split("\n"):
        line = line.strip()
        if line and not line.startswith("#"):
            hashes.add(line.lower())

    return hashes


def _scan_tracked_files(
    tree_root: Path,
    denylist: Set[str],
    i6_words: Set[str],
) -> list[tuple[str, int, str]]:
    """Scan git-tracked files for forbidden names and I6 words.

    Args:
        tree_root: Root path of the repository.
        denylist: Set of forbidden name hashes.
        i6_words: Set of I6 words to match (already normalized).

    Returns:
        List of tuples (file_path, line_number, rule_id) for each hit.
    """
    results = []

    # Get list of git-tracked files
    try:
        output = subprocess.run(
            ["git", "ls-files"],
            cwd=str(tree_root),
            capture_output=True,
            text=True,
            timeout=10,
        )
        if output.returncode != 0:
            # Not a git repo or git command failed; scan all files
            tracked_files = []
        else:
            tracked_files = [tree_root / p for p in output.stdout.splitlines()]
    except (subprocess.TimeoutExpired, FileNotFoundError):
        # git not available or timed out; scan all files
        tracked_files = []

    if not tracked_files:
        # Fall back to scanning all files matching patterns
        for pattern in TRACKABLE_PATTERNS:
            tracked_files.extend(tree_root.rglob(pattern))
        tracked_files = list(set(tracked_files))  # Remove duplicates

    # Scan each file
    for file_path in tracked_files:
        # Skip directories
        if not file_path.is_file():
            continue

        # Skip exempt paths
        if _is_exempt(file_path, tree_root):
            continue

        # Skip special content kinds (scanned separately)
        file_str = str(file_path)
        if (
            file_str.endswith(".cassette.json")
            or file_str.endswith(".results.json")
            or file_str.endswith(".mermaid")
        ):
            continue

        try:
            content = file_path.read_text(errors="ignore")
        except (OSError, UnicodeDecodeError):
            # Skip files that can't be read
            continue

        # Scan each line
        for line_num, line in enumerate(content.split("\n"), start=1):
            tokens = _get_normalized_tokens(line)
            if not tokens:
                continue

            # Check for R7 violations (hashed names)
            if denylist:
                ngram_hashes = _compute_ngram_hashes(tokens)
                if ngram_hashes & denylist:  # Intersection check
                    results.append((str(file_path), line_num, "R7"))

            # Check for I6 violations (forbidden words)
            if i6_words and _match_i6_word(tokens, i6_words):
                # Skip if this is the i6_words.txt file itself
                if "i6_words.txt" not in str(file_path):
                    results.append((str(file_path), line_num, "I6"))

    return results


def _scan_content_lines(
    content: str,
    denylist: Set[str],
    i6_words: Set[str],
) -> list[tuple[int, str]]:
    """Scan text content lines for forbidden names and I6 words.

    Used for commit messages and PR/issue payloads.

    Args:
        content: Text content.
        denylist: Set of forbidden name hashes.
        i6_words: Set of I6 words (normalized).

    Returns:
        List of tuples (line_number, rule_id) for each hit.
    """
    results = []

    for line_num, line in enumerate(content.split("\n"), start=1):
        tokens = _get_normalized_tokens(line)
        if not tokens:
            continue

        # Check for R7 violations (hashed names)
        if denylist:
            ngram_hashes = _compute_ngram_hashes(tokens)
            if ngram_hashes & denylist:
                results.append((line_num, "R7"))

        # Check for I6 violations (forbidden words)
        if i6_words and _match_i6_word(tokens, i6_words):
            results.append((line_num, "I6"))

    return results


def scan_tree(
    tree_root: Path,
    denylist: Set[str],
    i6_words: Set[str],
) -> list[tuple[str, int, str]]:
    """Scan tracked files and content for forbidden names and I6 words.

    Args:
        tree_root: Root path of the repository.
        denylist: Set of forbidden name hashes.
        i6_words: Set of I6 words to match (whole word, case-insensitive).

    Returns:
        List of tuples (file_path, line_number, rule_id) for each hit.
    """
    results = []

    # Normalize I6 words for matching
    normalized_i6 = {unicodedata.normalize("NFKC", w).lower() for w in i6_words}

    # Scan tracked files
    results.extend(_scan_tracked_files(tree_root, denylist, normalized_i6))

    # Scan cassette files
    for cassette_file in tree_root.rglob("*.cassette.json"):
        if _is_exempt(cassette_file, tree_root):
            continue
        try:
            content = cassette_file.read_text(errors="ignore")
            for line_num, line in enumerate(content.split("\n"), start=1):
                tokens = _get_normalized_tokens(line)
                if not tokens:
                    continue

                if denylist:
                    ngram_hashes = _compute_ngram_hashes(tokens)
                    if ngram_hashes & denylist:
                        results.append((str(cassette_file), line_num, "R7"))

                if normalized_i6 and _match_i6_word(tokens, normalized_i6):
                    results.append((str(cassette_file), line_num, "I6"))
        except (OSError, UnicodeDecodeError):
            pass

    # Scan diagram files
    for diagram_file in tree_root.rglob("*.mermaid"):
        if _is_exempt(diagram_file, tree_root):
            continue
        try:
            content = diagram_file.read_text(errors="ignore")
            for line_num, line in enumerate(content.split("\n"), start=1):
                tokens = _get_normalized_tokens(line)
                if not tokens:
                    continue

                if denylist:
                    ngram_hashes = _compute_ngram_hashes(tokens)
                    if ngram_hashes & denylist:
                        results.append((str(diagram_file), line_num, "R7"))

                if normalized_i6 and _match_i6_word(tokens, normalized_i6):
                    results.append((str(diagram_file), line_num, "I6"))
        except (OSError, UnicodeDecodeError):
            pass

    # Scan results files
    for results_file in tree_root.rglob("*.results.json"):
        if _is_exempt(results_file, tree_root):
            continue
        try:
            content = results_file.read_text(errors="ignore")
            for line_num, line in enumerate(content.split("\n"), start=1):
                tokens = _get_normalized_tokens(line)
                if not tokens:
                    continue

                if denylist:
                    ngram_hashes = _compute_ngram_hashes(tokens)
                    if ngram_hashes & denylist:
                        results.append((str(results_file), line_num, "R7"))

                if normalized_i6 and _match_i6_word(tokens, normalized_i6):
                    results.append((str(results_file), line_num, "I6"))
        except (OSError, UnicodeDecodeError):
            pass

    return results


def scan_payload(
    content: str,
    denylist: Set[str],
    i6_words: Set[str],
) -> list[tuple[int, str]]:
    """Scan commit message or PR/issue text payload for forbidden names and I6 words.

    Args:
        content: Text content (commit message, PR body, etc.).
        denylist: Set of forbidden name hashes.
        i6_words: Set of I6 words to match (whole word, case-insensitive).

    Returns:
        List of tuples (line_number, rule_id) for each hit.
    """
    # Normalize I6 words for matching
    normalized_i6 = {unicodedata.normalize("NFKC", w).lower() for w in i6_words}

    return _scan_content_lines(content, denylist, normalized_i6)
