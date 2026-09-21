"""Cohort profile configuration loading."""

from dataclasses import dataclass


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
    raise NotImplementedError("load_cohort_profile not yet implemented")
