"""Tests for hardware tier detection and resolution (AC1, AC2, AC3)."""

from pathlib import Path
from unittest.mock import patch

import pytest

from clinicloop.setup.tiers import (
    UnsupportedMemoryTier,
    load_tiers,
    resolve_tier,
)


@pytest.fixture
def hardware_tiers_path() -> Path:
    """Return path to hardware_tiers.toml in the source tree."""
    return (
        Path(__file__).parent.parent.parent / "src" / "clinicloop" / "setup" / "hardware_tiers.toml"
    )


@pytest.fixture
def incomplete_tiers_path(tmp_path: Path) -> Path:
    """Return path to a fixture hardware_tiers.toml with quantisation key deleted."""
    config_path = tmp_path / "hardware_tiers.toml"

    # Copy the real config but remove quantisation from the first row
    content = """
[[tier]]
label = "64GB+"
min_gib = 64
repo_id = "unsloth/Qwen3-30B-A3B-Instruct-2507-GGUF"
fallback_repo_id = "unsloth/Mistral-Small-3.2-24B-Instruct-2506-GGUF"
provenance = "assumed"

[[tier]]
label = "48GB"
min_gib = 48
repo_id = "unsloth/Qwen3-30B-A3B-Instruct-2507-GGUF"
quantisation = "Q4_K_M"
fallback_repo_id = "unsloth/Mistral-Small-3.2-24B-Instruct-2506-GGUF"
provenance = "assumed"
"""
    config_path.write_text(content)
    return config_path


@pytest.mark.checklist_id("L4")
def test_four_rows_load_from_config_and_48gib_resolves_to_its_own_row(
    hardware_tiers_path: Path,
) -> None:
    """Load four rows from hardware_tiers.toml; 48 GiB resolves to 48GB row."""
    tiers = load_tiers(hardware_tiers_path)

    # Check exactly four tiers
    assert len(tiers) == 4

    labels = [t["label"] for t in tiers]
    assert labels == ["64GB+", "48GB", "32GB", "16GB"]

    min_gibs = [t["min_gib"] for t in tiers]
    assert min_gibs == [64, 48, 32, 16]

    # Test with 48 GiB mocked memory
    with patch("clinicloop.setup.tiers.get_available_memory_gib", return_value=48):
        selected = resolve_tier(tiers)
        assert selected["label"] == "48GB", "48 GiB should resolve to 48GB row, not 32GB row"


def test_missing_quantisation_key_raises_validation_error(
    incomplete_tiers_path: Path,
) -> None:
    """Loading a config with deleted quantisation key raises validation error."""
    with pytest.raises(ValueError) as exc_info:
        load_tiers(incomplete_tiers_path)

    # Error message should name the key and the row
    error_msg = str(exc_info.value).lower()
    assert "quantisation" in error_msg, "Error should mention missing 'quantisation' key"


@pytest.mark.checklist_id("L4")
def test_each_mocked_tier_returns_its_configured_selection() -> None:
    """Each mocked memory tier returns its configured repo_id and quantisation."""
    hardware_tiers_path = (
        Path(__file__).parent.parent.parent / "src" / "clinicloop" / "setup" / "hardware_tiers.toml"
    )
    tiers = load_tiers(hardware_tiers_path)

    # Test 64 GiB
    with patch("clinicloop.setup.tiers.get_available_memory_gib", return_value=64):
        selected = resolve_tier(tiers)
        assert selected["repo_id"] == "unsloth/Qwen3-30B-A3B-Instruct-2507-GGUF"
        assert selected["quantisation"] == "Q4_K_M"
        assert selected["fallback_repo_id"] == "unsloth/Mistral-Small-3.2-24B-Instruct-2506-GGUF"

    # Test 48 GiB
    with patch("clinicloop.setup.tiers.get_available_memory_gib", return_value=48):
        selected = resolve_tier(tiers)
        assert selected["repo_id"] == "unsloth/Qwen3-30B-A3B-Instruct-2507-GGUF"
        assert selected["quantisation"] == "Q4_K_M"
        assert selected["fallback_repo_id"] == "unsloth/Mistral-Small-3.2-24B-Instruct-2506-GGUF"

    # Test 32 GiB
    with patch("clinicloop.setup.tiers.get_available_memory_gib", return_value=32):
        selected = resolve_tier(tiers)
        assert selected["repo_id"] == "Qwen/Qwen3-14B-GGUF"
        assert selected["quantisation"] == "Q4_K_M"

    # Test 16 GiB
    with patch("clinicloop.setup.tiers.get_available_memory_gib", return_value=16):
        selected = resolve_tier(tiers)
        assert selected["repo_id"] == "Qwen/Qwen3-8B-GGUF"
        assert selected["quantisation"] == "Q4_K_M"

    # Test 8 GiB (unsupported)
    with patch("clinicloop.setup.tiers.get_available_memory_gib", return_value=8):
        with pytest.raises(UnsupportedMemoryTier) as exc_info:
            resolve_tier(tiers)
        # Error message should contain the detected amount in GiB
        assert "8" in str(exc_info.value)


@pytest.mark.checklist_id("L4")
def test_every_row_is_marked_assumed_and_the_page_says_so(
    hardware_tiers_path: Path,
) -> None:
    """Every row marked 'assumed'; docs/setup/hardware-tiers.md references S1 ADR."""
    tiers = load_tiers(hardware_tiers_path)

    # Check every row has provenance = "assumed"
    provenances = {t["provenance"] for t in tiers}
    assert provenances == {"assumed"}, (
        f"Expected all rows to have provenance='assumed', got {provenances}"
    )

    # Check documentation page exists and contains the required statement
    # Path: tests/setup/test_tiers.py -> tests -> root
    docs_path = Path(__file__).parent.parent.parent / "docs" / "setup" / "hardware-tiers.md"
    assert docs_path.exists(), f"Documentation page not found at {docs_path}"

    docs_content = docs_path.read_text()
    assert "assumed" in docs_content.lower(), "Documentation should mention 'assumed' values"
    assert "docs/adr/llm-model-selection.md" in docs_content, (
        "Documentation should reference docs/adr/llm-model-selection.md"
    )
