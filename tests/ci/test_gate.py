"""AC1: make ci discovers and executes checks/*.sh in lexical order."""

import subprocess
import tempfile
from pathlib import Path


def test_local_gate_discovers_checks_in_checks_directory() -> None:
    """AC1: make ci discovers executable checks/*.sh files in lexical order."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create a fixture check script
        checks_dir = tmpdir_path / "checks"
        checks_dir.mkdir()

        fixture_check = checks_dir / "zz-fixture.sh"
        marker_file = tmpdir_path / ".fixture-check-ran"

        fixture_check.write_text(
            f"""#!/bin/bash
# Fixture check that writes a marker file
touch "{marker_file}"
exit 0
"""
        )
        fixture_check.chmod(0o755)

        # Run make ci in the temp directory
        # We only test the checks discovery part, not the full make ci
        cmd = (
            "export LC_ALL=C; "
            f"for check in {checks_dir}/*.sh; do "
            '[ -x "$check" ] || continue; '
            '"$check" || exit $?; '
            "done"
        )
        result = subprocess.run(
            ["bash", "-c", cmd],
            cwd=tmpdir_path,
            capture_output=True,
            text=True,
        )

        # Check that the fixture check was executed
        assert marker_file.exists(), (
            f"Fixture check did not execute. Expected marker file at {marker_file}. "
            f"stdout: {result.stdout}, stderr: {result.stderr}"
        )
        assert result.returncode == 0, (
            f"Check execution failed with return code {result.returncode}: "
            f"{result.stdout} {result.stderr}"
        )
