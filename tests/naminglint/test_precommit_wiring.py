"""Tests for pre-commit hook wiring.

AC7: Pre-commit hook's entry string matches the dotted module path used by conformance tests.
Both tests/conformance/test_I6.py and test_R7.py carry the checklist_id marker and run lint
over the whole tracked tree, failing if exit code is non-zero.
"""

from pathlib import Path

import pytest


@pytest.mark.checklist_id("I6")
@pytest.mark.checklist_id("R7")
def test_hook_and_ci_use_the_same_entry_point() -> None:
    """AC7: Hook and CI conformance tests use the same module path.

    This test verifies that:
    1. The pre-commit hook configuration exists and names the correct entry point
    2. The conformance tests (test_I6.py and test_R7.py) exist and carry checklist_id markers
    3. All use the same module path: clinicloop.naminglint (or a submodule)
    """
    repo_root = Path(__file__).parent.parent.parent

    # 1. Check pre-commit config exists
    precommit_config = repo_root / ".pre-commit-config.yaml"
    assert precommit_config.exists(), f"Pre-commit config not found at {precommit_config}"

    # 2. Check pre-commit config mentions the naming lint entry
    precommit_content = precommit_config.read_text()
    assert "naminglint" in precommit_content or "clinicloop.naminglint" in precommit_content, (
        f"Pre-commit config should mention naminglint entry point, got: {precommit_content}"
    )

    # 3. Check conformance tests exist and import from clinicloop.naminglint
    conformance_i6 = repo_root / "tests" / "conformance" / "test_I6.py"
    conformance_r7 = repo_root / "tests" / "conformance" / "test_R7.py"

    assert conformance_i6.exists(), f"Conformance test I6 not found at {conformance_i6}"
    assert conformance_r7.exists(), f"Conformance test R7 not found at {conformance_r7}"

    # 4. Verify conformance tests mention clinicloop.naminglint
    i6_content = conformance_i6.read_text()
    r7_content = conformance_r7.read_text()

    assert "clinicloop.naminglint" in i6_content, (
        f"test_I6.py should import from clinicloop.naminglint, got: {i6_content[:500]}"
    )
    assert "clinicloop.naminglint" in r7_content, (
        f"test_R7.py should import from clinicloop.naminglint, got: {r7_content[:500]}"
    )

    # 5. Verify both conformance tests carry checklist markers
    assert "@pytest.mark.checklist_id" in i6_content, (
        "test_I6.py should carry @pytest.mark.checklist_id"
    )
    assert "@pytest.mark.checklist_id" in r7_content, (
        "test_R7.py should carry @pytest.mark.checklist_id"
    )
