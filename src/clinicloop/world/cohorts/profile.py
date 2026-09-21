"""Cohort profile configuration loading."""

import tomllib
from dataclasses import dataclass
from pathlib import Path


class CohortProfileIncomplete(Exception):
    """Raised when a required cohort profile field is missing."""

    pass


@dataclass
class CohortProfile:
    """Configuration for cohort generation.

    Attributes:
        cohort_count: Number of cohorts to generate.
        cases_per_cohort: Number of cases per cohort.
        assumed: Whether this is an assumed profile.
        assumption_note: Note about the assumptions.
    """

    cohort_count: int
    cases_per_cohort: int
    assumed: bool
    assumption_note: str


def load_cohort_profile() -> CohortProfile:
    """Load cohort profile from configuration file.

    Reads src/clinicloop/world/config/cohorts.toml and validates
    required fields.

    Returns:
        A CohortProfile with loaded configuration.

    Raises:
        CohortProfileIncomplete: If required fields are missing.
    """
    # Find the config file relative to this module
    config_file = Path(__file__).parent.parent / "config" / "cohorts.toml"

    if not config_file.exists():
        raise FileNotFoundError(f"Cohort config file not found: {config_file}")

    with open(config_file, "rb") as f:
        config = tomllib.load(f)

    cohorts_config = config.get("cohorts", {})

    required_fields = ["cohort_count", "cases_per_cohort", "assumed", "assumption_note"]
    for field in required_fields:
        if field not in cohorts_config:
            raise CohortProfileIncomplete(f"Missing required field: {field}")

    return CohortProfile(
        cohort_count=cohorts_config["cohort_count"],
        cases_per_cohort=cohorts_config["cases_per_cohort"],
        assumed=cohorts_config["assumed"],
        assumption_note=cohorts_config["assumption_note"],
    )
