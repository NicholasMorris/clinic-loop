"""Helper functions for documentation tests.

This module provides utilities for testing MkDocs builds and ADR files.
These functions are outside src/ so they return sentinels rather than raising exceptions.
"""

import subprocess
import tempfile
from pathlib import Path
from typing import Any


def build_site(docs_dir: Path, strict: bool = True) -> int:
    """Build the MkDocs site and return the exit code.

    Returns a sentinel value (2) instead of raising exceptions.
    This function is outside src/, so test assertions will catch the failure.

    Args:
        docs_dir: Path to the docs directory.
        strict: Whether to enable strict mode.

    Returns:
        The exit code from mkdocs build, or 2 if an error occurs.
    """
    try:
        cmd = ["mkdocs", "build", "--docs-dir", str(docs_dir)]
        if strict:
            cmd.append("--strict")
        result = subprocess.run(
            cmd,
            cwd=docs_dir.parent,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.returncode
    except Exception:
        return 2


def parse_adr(adr_path: Path) -> dict[str, bool]:
    """Parse an ADR file and check for required heading sections.

    Returns an empty mapping on any error (sentinel value).
    This allows tests outside src/ to assert the presence of sections.

    Args:
        adr_path: Path to the ADR markdown file.

    Returns:
        A mapping of required section names to True if present, empty dict on error.
    """
    required_sections = {
        "Status",
        "Context",
        "Decision",
        "Consequences",
        "Alternatives considered",
    }
    found_sections = set()

    try:
        content = adr_path.read_text(encoding="utf-8")
        for section in required_sections:
            # Look for markdown headings (## or ###)
            if f"## {section}" in content or f"### {section}" in content:
                found_sections.add(section)
    except Exception:
        return {}

    return {section: section in found_sections for section in required_sections}
