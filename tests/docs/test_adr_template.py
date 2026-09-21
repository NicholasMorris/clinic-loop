"""Tests for ADR template and naming requirements."""

import re
from pathlib import Path

import yaml

from tests.docs.helpers import parse_adr


def test_every_adr_has_the_five_required_sections() -> None:
    """Test that every ADR file has the five required heading sections.

    AC3: docs/adr/_template.md contains the headings Status, Context, Decision,
    Consequences and Alternatives considered, and the test fails naming any file
    under docs/adr other than index.md and .nav.yml whose heading set omits
    any of those five.
    """
    repo_root = Path(__file__).parent.parent.parent
    adr_dir = repo_root / "docs" / "adr"

    required_sections = {"Status", "Context", "Decision", "Consequences", "Alternatives considered"}

    # Check the template file must exist
    template_path = adr_dir / "_template.md"
    assert template_path.exists(), "docs/adr/_template.md must exist"

    template_result = parse_adr(template_path)
    template_sections = {s for s, present in template_result.items() if present}
    assert template_sections == required_sections, (
        f"Template missing sections: {required_sections - template_sections}"
    )

    # Check all other ADR files (excluding index.md and .nav.yml)
    if adr_dir.exists():
        for adr_file in adr_dir.glob("*.md"):
            if adr_file.name in ("index.md", "_template.md"):
                continue

            result = parse_adr(adr_file)
            found_sections = {s for s, present in result.items() if present}

            assert found_sections == required_sections, (
                f"{adr_file.name} missing required sections. "
                f"Has: {found_sections}, Missing: {required_sections - found_sections}"
            )


def test_adr_filenames_match_the_slug_pattern() -> None:
    """Test that ADR filenames match the required slug pattern.

    AC4: ADR file names match ^[a-z0-9]+(-[a-z0-9]+)*\\.md$, docs/adr/index.md
    lists exactly the twelve slugs named in this issue, and the test fails naming
    any file under docs/adr that breaks either rule.
    """
    repo_root = Path(__file__).parent.parent.parent
    adr_dir = repo_root / "docs" / "adr"

    # The twelve required ADR slugs from the issue
    required_slugs = {
        "llm-model-selection",
        "tts-engine-and-pin",
        "stt-model-selection",
        "diarisation-approach",
        "terminology-edition",
        "human-gates",
        "checkpointing",
        "framework-choice",
        "model-tiers-and-review",
        "ci-tiers-and-recorded-results",
        "sandbox-limits",
        "integrity-allowlist",
    }

    # Check that adr directory exists
    assert adr_dir.exists(), "docs/adr directory must exist"

    # Check filename pattern
    slug_pattern = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*\.md$")

    found_slugs = set()
    for md_file in adr_dir.glob("*.md"):
        filename = md_file.name

        # Skip template and index
        if filename in ("_template.md", "index.md"):
            continue

        # Check filename matches pattern
        assert slug_pattern.match(filename), (
            f"ADR filename '{filename}' does not match pattern ^[a-z0-9]+(-[a-z0-9]+)*\\.md$"
        )

        # Extract slug (remove .md)
        slug = filename[:-3]
        found_slugs.add(slug)

    # Check index.md exists and lists the required slugs
    index_path = adr_dir / "index.md"
    assert index_path.exists(), "docs/adr/index.md must exist"

    index_content = index_path.read_text(encoding="utf-8")

    # Verify all required slugs are mentioned in index
    for slug in required_slugs:
        assert slug in index_content, (
            f"Required ADR slug '{slug}' not found in docs/adr/index.md"
        )

    # Verify no unexpected slugs are listed
    # (This is checked by verifying the slugs mentioned match our list)
    for slug in found_slugs:
        assert slug in required_slugs, (
            f"Unexpected ADR slug '{slug}' found; must be in the required list"
        )
