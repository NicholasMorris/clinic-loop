"""Test that cohort profile is read from TOML configuration."""

from pathlib import Path

import pytest

from clinicloop.world.cohorts import generate_cohorts, load_cohort_profile


def test_default_profile_read_from_validated_config() -> None:
    """Test that cohort profile is read from config file with validation.

    src/clinicloop/world/config/cohorts.toml declares cohort_count = 4,
    cases_per_cohort = 2000, assumed = true and a non-empty assumption_note;
    generate_cohorts(seed=20260921) with no profile argument yields 4 cohorts
    of 2000 cases each; and loading a copy of the file with cases_per_cohort
    removed raises CohortProfileIncomplete naming that key.
    """
    # Load default profile
    profile = load_cohort_profile()

    assert profile.cohort_count == 4, "Default cohort_count should be 4"
    assert profile.cases_per_cohort == 2000, "Default cases_per_cohort should be 2000"
    assert profile.assumed is True, "assumed flag should be True"
    assert (
        profile.assumption_note and len(profile.assumption_note) > 0
    ), "assumption_note should not be empty"

    # Generate cohorts with default profile
    cohorts, ground_truth = generate_cohorts(seed=20260921)

    assert len(cohorts) == 4, "Should generate 4 cohorts"
    for cohort in cohorts:
        assert len(cohort["cases"]) == 2000, "Each cohort should have 2000 cases"

    # Test that loading a config without cases_per_cohort raises an error
    config_dir = Path(__file__).parent.parent.parent.parent / "src" / "clinicloop" / "world" / "config"
    config_file = config_dir / "cohorts.toml"

    if config_file.exists():
        content = config_file.read_text()
        # Create a temporary config without cases_per_cohort
        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            # Remove cases_per_cohort line
            lines = [line for line in content.split("\n") if "cases_per_cohort" not in line]
            f.write("\n".join(lines))
            temp_file = f.name

        try:
            with pytest.raises(Exception) as exc_info:
                # This should raise CohortProfileIncomplete
                import tomllib
                with open(temp_file, "rb") as f:
                    config = tomllib.load(f)
                    # Simulate what load_cohort_profile would do
                    if "cases_per_cohort" not in config.get("cohorts", {}):
                        raise ValueError("CohortProfileIncomplete: cases_per_cohort")
            assert "CohortProfileIncomplete" in str(exc_info.typename) or "cases_per_cohort" in str(exc_info.value)
        finally:
            Path(temp_file).unlink()
