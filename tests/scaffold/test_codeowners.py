"""Tests for CODEOWNERS file."""

from pathlib import Path


def get_codeowners_path() -> Path:
    """Get the path to CODEOWNERS file."""
    return Path(__file__).parent.parent.parent / "CODEOWNERS"


def test_every_gate_critical_prefix_has_an_owner() -> None:
    """Test that all gate-critical prefixes have CODEOWNERS entries.

    AC6: CODEOWNERS assigns an owner to each of the prefixes
    scripts/process/**, checks/**, src/clinicloop/naminglint/**,
    src/clinicloop/compliance/**, src/clinicloop/evals/thresholds*,
    src/clinicloop/agents/integrity/forbidden_features* and
    docs/process/**, and the test fails naming any of those seven
    prefixes with no matching entry.
    """
    codeowners_path = get_codeowners_path()
    assert codeowners_path.exists(), f"CODEOWNERS file not found at {codeowners_path}"

    codeowners_content = codeowners_path.read_text()

    required_prefixes = [
        "scripts/process/**",
        "checks/**",
        "src/clinicloop/naminglint/**",
        "src/clinicloop/compliance/**",
        "src/clinicloop/evals/thresholds",
        "src/clinicloop/agents/integrity/forbidden_features",
        "docs/process/**",
    ]

    for prefix in required_prefixes:
        # Check if the prefix appears in CODEOWNERS
        assert prefix in codeowners_content, f"Prefix '{prefix}' not found in CODEOWNERS"

        # Find the line containing this prefix and check it has an owner
        for line in codeowners_content.split("\n"):
            if prefix in line and not line.strip().startswith("#"):
                # Should have format: <pattern> <owner>
                parts = line.split()
                assert len(parts) >= 2, f"CODEOWNERS entry for '{prefix}' has no owner assigned"
                break
