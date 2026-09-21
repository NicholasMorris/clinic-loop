"""Tests for setup command (AC5)."""

from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from clinicloop.setup.doctor import run_doctor
from clinicloop.setup.install import run_setup


@pytest.mark.checklist_id("L4")
def test_written_selection_is_read_back_by_doctor(tmp_path: Path) -> None:
    """Setup writes selection to config; doctor reads it back."""
    hardware_tiers_path = (
        __file__.rsplit("/", 3)[0]  # get the repo root
        + "/src/clinicloop/setup/hardware_tiers.toml"
    )
    config_file = tmp_path / "models.toml"

    # Mock binaries as present
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

    # Mock package manager
    mock_package_manager = MagicMock()

    with patch("clinicloop.setup.doctor.find_binary", side_effect=find_binary):
        with patch("clinicloop.setup.doctor.get_binary_version", side_effect=get_version):
            with patch("clinicloop.setup.doctor.get_available_memory_gib", return_value=32):
                # Run setup
                with patch(
                    "clinicloop.setup.install.find_binary",
                    side_effect=find_binary,
                ):
                    with patch(
                        "clinicloop.setup.install.get_available_memory_gib", return_value=32
                    ):
                        with patch(
                            "clinicloop.setup.install.run_package_manager",
                            mock_package_manager,
                        ):
                            with patch("sys.stdout", StringIO()):
                                run_setup(
                                    hardware_tiers_path,
                                    config_path=config_file,
                                )

                # Check config file was written
                assert config_file.exists(), f"Config file should be written to {config_file}"

                # Run doctor to verify it can read back the same values
                with patch("sys.stdout", StringIO()):
                    # Create a temporary models.toml that doctor can read
                    # We need to tell doctor to read from this file
                    exit_code = run_doctor(
                        hardware_tiers_path,
                        config_path=config_file,
                    )

                assert exit_code == 0, "doctor should succeed reading written config"


def test_setup_invokes_package_manager_for_ffmpeg_when_absent(tmp_path: Path) -> None:
    """Setup invokes package manager once with ffmpeg install when ffmpeg absent."""
    hardware_tiers_path = (
        __file__.rsplit("/", 3)[0]  # get the repo root
        + "/src/clinicloop/setup/hardware_tiers.toml"
    )
    config_file = tmp_path / "models.toml"

    # Mock ffmpeg as absent, whisper.cpp as present
    def find_binary(name: str) -> str | None:
        if name == "ffmpeg":
            return None
        elif name == "whisper.cpp":
            return "/usr/local/bin/whisper-cpp"
        return None

    mock_package_manager = MagicMock()

    with patch("clinicloop.setup.install.find_binary", side_effect=find_binary):
        with patch("clinicloop.setup.install.get_available_memory_gib", return_value=32):
            with patch(
                "clinicloop.setup.install.run_package_manager",
                mock_package_manager,
            ):
                with patch("sys.stdout", StringIO()):
                    run_setup(
                        hardware_tiers_path,
                        config_path=config_file,
                    )

    # Verify package manager was called exactly once for ffmpeg
    mock_package_manager.assert_called_once()
    args = mock_package_manager.call_args[0] if mock_package_manager.call_args else []
    assert len(args) > 0
    command = " ".join(args[0]) if isinstance(args[0], list) else str(args[0])
    assert "ffmpeg" in command.lower(), "Package manager should be called for ffmpeg install"


def test_setup_prints_whisper_cpp_build_instructions(tmp_path: Path) -> None:
    """Setup prints whisper.cpp build instructions when binary absent."""
    hardware_tiers_path = (
        __file__.rsplit("/", 3)[0]  # get the repo root
        + "/src/clinicloop/setup/hardware_tiers.toml"
    )
    config_file = tmp_path / "models.toml"

    # Mock ffmpeg as present, whisper.cpp as absent
    def find_binary(name: str) -> str | None:
        if name == "ffmpeg":
            return "/usr/bin/ffmpeg"
        elif name == "whisper.cpp":
            return None
        return None

    with patch("clinicloop.setup.install.find_binary", side_effect=find_binary):
        with patch("clinicloop.setup.install.get_available_memory_gib", return_value=32):
            with patch("clinicloop.setup.install.run_package_manager"):
                captured_output = StringIO()
                with patch("sys.stdout", captured_output):
                    run_setup(
                        hardware_tiers_path,
                        config_path=config_file,
                    )

                output = captured_output.getvalue()
                assert "whisper" in output.lower(), "Should print whisper.cpp build instructions"
