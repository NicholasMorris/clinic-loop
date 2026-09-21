# Cohort Generation and Confound Planting

## Overview

Cohorts are synthetic populations with equal true base rates of integrity signals by design, distinguished only by which confound is dense in them. This design isolates the causal effect of confounds on flag rates, enabling the bias evaluation to report and mitigate disparities.

## Structure

A cohort is identified by its dense confound, not by demographic attributes. Four cohorts are shipped by default:
- Cohort A: Household-shared payment instruments (dense)
- Cohort B: Renter address churn (dense)
- Cohort C: Transliteration variance in names (dense)
- Cohort D: First-of-January dates of birth (dense)

Each cohort contains an equal number of cases (2000 by default), and the true base rate of each integrity signal is identical across all cohorts within sampling noise.

## Planted Confounds

Confounds are account-level factors that can influence flag rates without being signals. The five confound types planted in each cohort are:

### 1. Household-Shared Instruments
Multiple patients in the cohort share the same payment instrument ID. This reflects legitimate patterns (family members, household sharing) and tests whether the reused-instrument signal has higher flag rates in this cohort.

### 2. Renter Address Churn
Patients in this cohort have frequent address changes, reflecting renter mobility. The signal extraction rules ignore format-only changes and count distinct addresses only within a year, preventing false positives.

### 3. Transliteration Variance
Names appear in multiple romanizations (e.g., "Nikolai" and "Nikolay"). The duplicate-identity signal uses exact hashed keys, not phonetic matching, so this confound tests noise introduced by data entry variation.

### 4. First-of-January Dates of Birth
A higher proportion of patients have DOB on 01-January. This is a data-quality marker rather than a behavioral signal. The DOB-change signal ignores format-only and 01-January changes by design.

### 5. Multigenerational Payment Instruments
The same payment instrument is used by patients with very different ages (detected as DOB differences). This tests whether the reused-instrument signal triggers on accounts with shared instruments across generations (e.g., joint family accounts).

## Integrity Signals

The same five signal types are planted with equal base rates across all cohorts:

1. **Duplicate Identity**: Exact match on full name and date of birth (across two or more accounts)
2. **Reused Instrument**: Same payment_instrument_id (across two or more accounts)
3. **Template Language**: Questionnaire text matches known templates or forum text
4. **Consult-Shopping**: Multiple consultations with different clinicians within a short window
5. **Velocity**: Unusual rate of orders or account changes

Each signal is planted in 15% of patients across all cohorts. The ground-truth records which signals were planted per patient, enabling exact measurement of flag precision and recall.

## Configuration

Cohort counts and sizes are read from `src/clinicloop/world/config/cohorts.toml`, not coded as defaults:

```toml
[cohorts]
cohort_count = 4
cases_per_cohort = 2000
assumed = true
assumption_note = "Starter values sized for bootstrap intervals in M3-4 bias evaluation..."
```

### Profile Validation

The `load_cohort_profile()` function reads this configuration and validates that all required fields are present. If a field is missing, it raises `CohortProfileIncomplete` naming the field.

**Rationale**: Counts and sizes are not defaulted in code because the bias evaluation (M3-4) may change them for different statistical power. Editing the config file is clearer than re-running the generator with different arguments.

## Protected Attributes

Cohort case records deliberately omit demographic and identifying information to prevent proxy-based discrimination:

- No postcode, suburb, or state
- No ethnicity, name origin, or age
- No gender, employment status, or language
- No date of birth (identified values only through keyed-hash pseudonyms at ingress)
- No full name or street address

This design aligns with requirement I3 (Forbidden signals) and prevents detectors from accidentally using proxies even if available.

## Cohort Labels and Ground Truth

Cohort membership labels are stored in a separate ground-truth export, not in the case records themselves. This separation ensures that:

1. Case records can be processed by detectors without revealing cohort identity
2. Ground truth for evaluation can be kept separate and secure
3. Bias analysis can compare flag rates across cohorts without contaminating detector training

Ground truth format: `(patient_id, signals_set, confounds_set)`
- `patient_id`: Synthetic patient identifier
- `signals_set`: Set of signal types planted in this patient
- `confounds_set`: Set of confound types present in this patient

## Message Corpus

A templated message corpus is built alongside cohorts for the triage golden set. Each message is:

- Generated from one of 8+ templates per intent
- Marked with `generation_method = "templated"` and a resolvable `template_id`
- Labelled with intent (order_status, cancellation, delivery_problem, general_question, dose_question, adverse_event, pregnancy, mental_health_distress, product_name_request, prompt_injection)
- Assigned `must_escalate = True` for adverse_event, pregnancy, mental_health_distress, dose_question, product_name_request, and prompt_injection

The corpus covers three golden scenarios:
- ps-03: Termination cutoff message patterns
- ps-04: Damaged-item intake patterns
- po-01: Payment-to-dispatch stall alert patterns

## Reproducibility

All cohort and corpus generation is deterministic: calling `generate_cohorts(seed=X)` twice produces identical outputs. Changing the seed produces a different dataset with the same structure.

## Flag-Rate Disparity Metric

The flag-rate disparity report is built and owned by M3-4 (Bias Evaluation). This issue provides the substrate (equal-base-rate cohorts with planted confounds) and the ground truth. The bias evaluation:

1. Runs detectors on the cohort cases
2. Compares flag rates across cohorts
3. Reports disparity (difference between cohorts) with bootstrap confidence intervals
4. Examines which confounds explain the disparity
5. Assesses mitigations and their recall cost

A disparity, once baselined, is documented in `docs/known-disparities.md` with an owner and mitigation plan, not silently accepted or hidden.

## Naming Convention

This component is always called "cohort generation" or "confound planting" in prose, never "demographic stratification" (which would suggest demographic intent). Confounds are not demographic attributes and the cohorts have no demographic axis.
