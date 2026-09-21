"""Tests for doctor command (AC4, AC6)."""

import socket
from io import StringIO
from unittest.mock import patch

import pytest

from clinicloop.setup.doctor import run_doctor


@pytest.mark.checklist_id("L4")
def test_missing_external_binaries_are_named_and_exit_is_one() -> None:
    """Doctor exits 1, naming each missing binary (ffmpeg, whisper.cpp)."""
    hardware_tiers_path = (
        __file__.rsplit("/", 3)[0]  # get the repo root
        + "/src/clinicloop/setup/hardware_tiers.toml"
    )

    # Mock both binaries as missing
    with patch("clinicloop.setup.doctor.find_binary", return_value=None):
        # Capture output
        captured_output = StringIO()
        with patch("sys.stdout", captured_output):
            exit_code = run_doctor(hardware_tiers_path)

        assert exit_code == 1, "Should exit with code 1 when binaries missing"
        output = captured_output.getvalue()
        assert "ffmpeg" in output.lower(), "Should name ffmpeg as missing"
        assert "whisper" in output.lower(), "Should name whisper.cpp as missing"

    # Mock only ffmpeg as present
    def find_binary_ffmpeg(name: str) -> str | None:
        if name == "ffmpeg":
            return "/usr/bin/ffmpeg"
        return None

    with patch("clinicloop.setup.doctor.find_binary", side_effect=find_binary_ffmpeg):
        with patch("clinicloop.setup.doctor.get_binary_version", return_value="6.0"):
            captured_output = StringIO()
            with patch("sys.stdout", captured_output):
                exit_code = run_doctor(hardware_tiers_path)

            assert exit_code == 1, "Should exit 1 when whisper.cpp missing"
            output = captured_output.getvalue()
            assert "whisper" in output.lower(), "Should name whisper.cpp as missing"


@pytest.mark.checklist_id("L4")
def test_doctor_with_both_binaries_present_exits_zero() -> None:
    """Doctor exits 0 and prints version strings when both binaries present."""
    hardware_tiers_path = (
        __file__.rsplit("/", 3)[0]  # get the repo root
        + "/src/clinicloop/setup/hardware_tiers.toml"
    )

    # Mock both binaries as present
    def find_binary(name: str) -> str | None:
        if name == "ffmpeg":
            return "/usr/bin/ffmpeg"
        elif name == "whisper.cpp":
            return "/usr/local/bin/whisper-cpp"
        return None

    def get_version(binary_path: str) -> str:
        if "ffmpeg" in binary_path:
            return "ffmpeg-6.0"
        return "whisper-cpp-1.0.0"

    with patch("clinicloop.setup.doctor.find_binary", side_effect=find_binary):
        with patch("clinicloop.setup.doctor.get_binary_version", side_effect=get_version):
            with patch("clinicloop.setup.doctor.get_available_memory_gib", return_value=32):
                captured_output = StringIO()
                with patch("sys.stdout", captured_output):
                    exit_code = run_doctor(hardware_tiers_path)

                assert exit_code == 0, "Should exit 0 when binaries present"
                output = captured_output.getvalue()
                # Should contain version information
                assert "ffmpeg" in output.lower() or "version" in output.lower()


@pytest.mark.checklist_id("L4")
def test_doctor_opens_no_socket() -> None:
    """Doctor returns same exit code regardless of socket.socket monkeypatch."""
    hardware_tiers_path = (
        __file__.rsplit("/", 3)[0]  # get the repo root
        + "/src/clinicloop/setup/hardware_tiers.toml"
    )

    # Mock both binaries as present with working versions
    def find_binary(name: str) -> str | None:
        if name == "ffmpeg":
            return "/usr/bin/ffmpeg"
        elif name == "whisper.cpp":
            return "/usr/local/bin/whisper-cpp"
        return None

    def get_version(binary_path: str) -> str:
        if "ffmpeg" in binary_path:
            return "ffmpeg-6.0"
        return "whisper-cpp-1.0.0"

    # Get exit code without socket monkeypatch
    with patch("clinicloop.setup.doctor.find_binary", side_effect=find_binary):
        with patch("clinicloop.setup.doctor.get_binary_version", side_effect=get_version):
            with patch("clinicloop.setup.doctor.get_available_memory_gib", return_value=32):
                with patch("sys.stdout", StringIO()):
                    exit_code_normal = run_doctor(hardware_tiers_path)

    # Get exit code with socket.socket monkeypatched to raise RuntimeError
    with patch.object(socket, "socket", side_effect=RuntimeError("No sockets!")):
        with patch("clinicloop.setup.doctor.find_binary", side_effect=find_binary):
            with patch("clinicloop.setup.doctor.get_binary_version", side_effect=get_version):
                with patch("clinicloop.setup.doctor.get_available_memory_gib", return_value=32):
                    with patch("sys.stdout", StringIO()):
                        exit_code_with_socket_patch = run_doctor(hardware_tiers_path)

    # Exit codes should be the same - doctor should not open a socket
    assert exit_code_normal == exit_code_with_socket_patch, (
        "doctor should not open sockets - exit code should be the same"
    )


def test_python_dash_m_runs_the_doctor_and_prints_the_tier() -> None:
    """`python -m clinicloop.setup.doctor` (what `make doctor` runs) must actually run."""
    import subprocess
    import sys

    result = subprocess.run(
        [sys.executable, "-m", "clinicloop.setup.doctor"], capture_output=True, text=True
    )
    assert "Hardware Tier:" in result.stdout, result.stdout + result.stderr


def test_find_binary_accepts_the_whisper_cli_name(tmp_path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """whisper.cpp 1.9 installs `whisper-cli`; the doctor must find it."""
    from clinicloop.setup import doctor

    fake = tmp_path / "whisper-cli"
    fake.write_text("#!/bin/sh\n")
    fake.chmod(0o755)
    monkeypatch.setenv("PATH", str(tmp_path))
    assert doctor.find_binary("whisper.cpp") == str(fake)
