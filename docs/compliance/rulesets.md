# Compliance Rulesets

## Overview

Rulesets define jurisdiction-specific compliance rules for the system. Each ruleset is keyed by a jurisdiction identifier and contains a list of rules with citations.

## File Layout

Rulesets are stored as YAML files in `src/clinicloop/compliance/rules/`:
- `au.yaml` - Australian jurisdiction (populated)
- `uk.yaml` - United Kingdom jurisdiction (stubbed)
- `nz.yaml` - New Zealand jurisdiction (stubbed)

## Jurisdiction Seam: Explicit vs. Unset

The system distinguishes between three cases when loading a ruleset:

### Explicit Jurisdiction (e.g., `load_ruleset("au")`)
When a jurisdiction is explicitly specified, the corresponding ruleset is loaded with `fallback_active=False`. This is the standard mode of operation when the system knows the applicable jurisdiction.

### Unimplemented Jurisdictions
When `load_ruleset("uk")` or `load_ruleset("nz")` is called explicitly, a `RulesetNotImplemented` exception is raised. The exception message includes the requested jurisdiction string. This prevents silent fallback to AU rules and ensures that unimplemented jurisdictions are detected.

### Unset Jurisdiction (e.g., `load_ruleset(None)`)
When no jurisdiction is specified (None), the AU ruleset is loaded with `fallback_active=True` and a non-empty `fallback_banner`. The banner carries a visible message indicating that AU rules are being used as a default. This design prevents silent authorization under unimplemented rules while making the fallback explicit and visible.

## Rule Structure

Each rule in a ruleset must contain:
- `rule_id` (required, non-empty string): A unique identifier for the rule
- `citation` (required): A citation block with the following fields:
  - `instrument` (string): The regulatory instrument (e.g., statute name)
  - `provision` (string): The specific provision or section (e.g., "Section 21")
  - `checked_date` (string): The date the citation was last verified
  - `citation_status` (string): One of `verified` or `unverified`

All rule IDs within a ruleset must be unique.

## Citation Status

Each rule carries a citation status indicating whether the cited provision has been verified against its source:

- **`unverified`**: The citation has not been confirmed against the source material. Unverified citations render visibly in outputs with a visual marker but are excluded from README and other published documentation, ensuring no unconfirmed citation is published as fact.

- **`verified`**: The citation has been confirmed against its source (typically by M7-2 citation checker). Only verified citations are included in published documentation.

## Loading Rulesets

```python
from clinicloop.compliance.rulesets import load_ruleset, RulesetNotImplemented

# Load AU ruleset explicitly
au_rules = load_ruleset("au")
print(au_rules.fallback_active)  # False

# Load with default (AU) fallback
default_rules = load_ruleset(None)
print(default_rules.fallback_active)  # True
print(default_rules.fallback_banner)  # Non-empty message

# Try to load unimplemented jurisdiction
try:
    uk_rules = load_ruleset("uk")
except RulesetNotImplemented as e:
    print(f"Jurisdiction not implemented: {e}")
```

## AU Ruleset

The AU (Australian) ruleset is populated with compliance rules applicable to the Australian healthcare and telehealth context. Each rule includes:
- A unique rule ID
- Citation information (instrument, provision, checked date, status)
- Human-readable description

Rules in the AU ruleset cover areas such as:
- Therapeutic Goods Act requirements
- National Health Act provisions
- Telehealth service standards
- Privacy and data protection requirements

## Future Jurisdictions

UK and NZ rulesets are stubbed (empty) and raise `RulesetNotImplemented` when explicitly requested. Adding support for these jurisdictions requires:
1. Populating the corresponding YAML file with rules
2. Verifying each rule's citation against source materials
3. Setting appropriate `citation_status` values
4. Adding corresponding tests

This phased approach ensures that unimplemented jurisdictions cannot silently use AU rules, and supports incremental expansion to new markets.
