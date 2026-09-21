"""Tests for the make ci target and its checks/*.sh discovery."""

import shutil
import stat
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

RECORDER = """#!/bin/sh
echo "$*" >> "$RECORD_LOG"
if [ -n "$FAIL_ON" ]; then
    case "$*" in
    *"$FAIL_ON"*) exit 3 ;;
    esac
fi
exit 0
"""


def make_checkout(root: Path) -> Path:
    """Create a temporary copy of the checkout holding the Makefile and checks/.

    Args:
        root: The directory to create the copy in, which must not exist yet.

    Returns:
        The path of the copy.
    """
    checkout = root
    checkout.mkdir()
    shutil.copy(REPO_ROOT / "Makefile", checkout / "Makefile")
    shutil.copytree(REPO_ROOT / "checks", checkout / "checks")
    return checkout


def write_check(checkout: Path, name: str, body: str, executable: bool = True) -> None:
    """Write a check script into the temporary checkout.

    Args:
        checkout: The temporary checkout.
        name: The script file name inside checks/.
        body: The shell body of the script.
        executable: Whether to set the executable bits.
    """
    script = checkout / "checks" / name
    script.write_text(f"#!/bin/sh\n{body}\n")
    executable_bits = stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
    script.chmod((script.stat().st_mode | executable_bits) if executable else 0o644)


def run_ci(checkout: Path, log: Path, fail_on: str = "") -> subprocess.CompletedProcess[str]:
    """Run make ci in the temporary checkout with the tool launcher replaced by a recorder.

    Args:
        checkout: The temporary checkout.
        log: The file the recorder and the checks append to.
        fail_on: A substring of a tool invocation that should make the recorder fail.

    Returns:
        The completed make process.
    """
    recorder = checkout / "recorder.sh"
    recorder.write_text(RECORDER)
    recorder.chmod(0o755)
    env = {"PATH": "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin", "FAIL_ON": fail_on}
    env["RECORD_LOG"] = str(log)
    return subprocess.run(
        ["make", "-C", str(checkout), "ci", f"RUN={recorder}"],
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )


def test_ci_target_discovers_unlisted_check(tmp_path: Path) -> None:
    """AC5: make ci runs the tools, then discovers and runs checks/*.sh in lexical order."""
    checkout = make_checkout(tmp_path / "all-pass")
    log = tmp_path / "all-pass.log"
    marker = tmp_path / "marker"
    write_check(checkout, "zz-fixture.sh", f'touch "{marker}"\necho zz >> "{log}"')
    write_check(checkout, "b-second.sh", f'echo b >> "{log}"')
    write_check(checkout, "a-first.sh", f'echo a >> "{log}"')
    write_check(checkout, "m-not-executable.sh", f'echo m >> "{log}"', executable=False)

    result = run_ci(checkout, log)
    assert result.returncode == 0, f"make ci failed:\n{result.stdout}\n{result.stderr}"
    assert marker.exists(), "unlisted zz-fixture.sh was not executed by make ci"

    lines = log.read_text().splitlines()
    assert [line.split()[0] for line in lines[:4]] == ["ruff", "ruff", "mypy", "pytest"], lines
    assert lines[0].startswith("ruff check"), lines
    assert lines[1].startswith("ruff format --check"), lines
    assert lines[4:] == ["a", "b", "zz"], f"checks not in lexical order, or ran m: {lines}"

    stopped = make_checkout(tmp_path / "check-fails")
    stopped_log = tmp_path / "check-fails.log"
    write_check(stopped, "a-first.sh", f'echo a >> "{stopped_log}"')
    write_check(stopped, "b-fails.sh", f'echo b >> "{stopped_log}"\nexit 7')
    write_check(stopped, "zz-fixture.sh", f'echo zz >> "{stopped_log}"')
    failed = run_ci(stopped, stopped_log)
    assert failed.returncode != 0, "make ci ignored a failing check"
    assert stopped_log.read_text().splitlines()[4:] == ["a", "b"], "checks ran past the failure"

    broken = make_checkout(tmp_path / "tool-fails")
    broken_log = tmp_path / "tool-fails.log"
    write_check(broken, "a-first.sh", f'echo a >> "{broken_log}"')
    tool_failed = run_ci(broken, broken_log, fail_on="mypy")
    assert tool_failed.returncode != 0, "make ci ignored a failing tool"
    ran = [line.split()[0] for line in broken_log.read_text().splitlines()]
    assert ran == ["ruff", "ruff", "mypy"], f"pytest or checks ran after mypy failed: {ran}"


def test_default_tool_launcher_uses_the_dev_extra() -> None:
    """Every tool in make ci runs through uv with the dev extra available."""
    dry = subprocess.run(
        ["make", "-n", "-C", str(REPO_ROOT), "ci"], capture_output=True, text=True, check=False
    )
    assert dry.returncode == 0, dry.stderr
    tool_lines = [line for line in dry.stdout.splitlines() if line.lstrip().startswith("uv run")]
    assert len(tool_lines) == 4, f"expected four tool invocations: {dry.stdout}"
    for line in tool_lines:
        assert "--extra dev" in line, f"tool line without the dev extra: {line}"
    assert any("pytest" in line and "not local_model" in line for line in tool_lines)
