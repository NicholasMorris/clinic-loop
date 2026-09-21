"""Tests for the CODEOWNERS file."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

GATE_CRITICAL_PREFIXES = [
    "scripts/process/**",
    "checks/**",
    "src/clinicloop/naminglint/**",
    "src/clinicloop/compliance/**",
    "src/clinicloop/evals/thresholds*",
    "src/clinicloop/agents/integrity/forbidden_features*",
    "docs/process/**",
]


def unowned_prefixes(codeowners: str) -> list[str]:
    """Return the gate-critical prefixes with no owned entry in a CODEOWNERS text.

    Args:
        codeowners: The CODEOWNERS file content.

    Returns:
        The prefixes that lack an entry naming at least one owner.
    """
    owned: set[str] = set()
    for line in codeowners.splitlines():
        fields = line.split()
        if len(fields) >= 2 and not fields[0].startswith("#") and fields[1].startswith("@"):
            owned.add(fields[0])
    return [prefix for prefix in GATE_CRITICAL_PREFIXES if prefix not in owned]


def test_every_gate_critical_prefix_has_an_owner() -> None:
    """AC6: each of the seven prefixes has an owner, and the check names any that lack one."""
    assert len(set(GATE_CRITICAL_PREFIXES)) == 7

    missing = unowned_prefixes((REPO_ROOT / "CODEOWNERS").read_text())
    assert not missing, f"no CODEOWNERS entry with an owner for: {missing}"

    without_checks = "\n".join(
        f"{prefix} @owner" for prefix in GATE_CRITICAL_PREFIXES if prefix != "checks/**"
    )
    assert unowned_prefixes(without_checks) == ["checks/**"]
    assert unowned_prefixes("checks/**\n# docs/process/** @owner") == GATE_CRITICAL_PREFIXES
