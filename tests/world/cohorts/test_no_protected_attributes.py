"""Test that cohort schema contains no protected attributes."""

from clinicloop.world.cohorts import generate_cohorts


def test_cohort_schema_carries_no_protected_attribute_names() -> None:
    """Test that cohort records do not carry protected attribute names.

    A field-name scan over the exported cohort schema finds none of postcode,
    suburb, state, ethnicity, name origin, age, gender, employment, language
    or country of birth among attribute or derived-column names, and each
    cohort's identity in the ground-truth record is the name of its dense
    confound.
    """
    cohorts, ground_truth = generate_cohorts(seed=20260921)

    protected_names = {
        "postcode",
        "suburb",
        "state",
        "ethnicity",
        "name_origin",
        "age",
        "gender",
        "employment",
        "language",
        "country_of_birth",
        # Also check common variations
        "nameorigin",
        "dob",
        "date_of_birth",
        "employment_status",
    }

    # Check all field names in cohort data
    for cohort_idx, cohort_data in enumerate(cohorts):
        # Check cohort metadata fields
        for key in cohort_data.keys():
            assert key.lower() not in protected_names, (
                f"Cohort {cohort_idx} contains protected field: {key}"
            )

        # Check case record fields
        for case in cohort_data.get("cases", []):
            for key in case.keys():
                assert key.lower() not in protected_names, (
                    f"Cohort {cohort_idx} case contains protected field: {key}"
                )

    # Check that each cohort's identity is the name of its dense confound
    confound_names = {
        "household_shared_instrument",
        "renter_address_churn",
        "transliteration_variance",
        "first_january_dob",
        "multigenerational_instrument",
    }

    for cohort_idx, cohort_data in enumerate(cohorts):
        cohort_identity = cohort_data.get("identity")
        assert cohort_identity is not None, f"Cohort {cohort_idx} does not have an identity field"
        assert cohort_identity in confound_names, (
            f"Cohort {cohort_idx} identity '{cohort_identity}' is not a confound name"
        )
