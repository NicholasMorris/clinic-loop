"""Conformance test for L4 requirement: LLM tier selection (AC7)."""

import re
from pathlib import Path

import pytest

from clinicloop.setup.tiers import load_tiers


@pytest.mark.checklist_id("L4")
def test_every_tier_row_names_a_repo_id_and_quantisation() -> None:
    """Every row in hardware_tiers.toml has valid repo_id and quantisation Q4_K_M."""
    hardware_tiers_path = (
        Path(__file__).parent.parent.parent
        / "src"
        / "clinicloop"
        / "setup"
        / "hardware_tiers.toml"
    )

    tiers = load_tiers(hardware_tiers_path)

    assert len(tiers) > 0, "Should have at least one tier row"

    repo_id_pattern = re.compile(r"^[A-Za-z0-9._-]+/[A-Za-z0-9._-]+$")

    for tier in tiers:
        # Check repo_id matches pattern
        repo_id = tier.get("repo_id")
        assert repo_id is not None, f"Tier {tier.get('label')} missing repo_id"
        assert repo_id_pattern.match(repo_id), (
            f"Tier {tier.get('label')}: repo_id '{repo_id}' "
            "does not match ^[A-Za-z0-9._-]+/[A-Za-z0-9._-]+$ pattern"
        )

        # Check quantisation is Q4_K_M (no placeholder)
        quantisation = tier.get("quantisation")
        assert quantisation is not None, f"Tier {tier.get('label')} missing quantisation"
        assert quantisation == "Q4_K_M", (
            f"Tier {tier.get('label')}: quantisation '{quantisation}' "
            "should be exactly 'Q4_K_M' (no placeholder allowed)"
        )
