# Ingress Module: PII Redaction and Pseudonymisation

## Overview

The ingress module provides the boundary where raw identifier values from external records are processed before being made available to the rest of the system. It performs two key functions:

1. **PII Redaction**: Removes personally identifiable information (PII) from text fields using pattern matching and checksum validation
2. **Pseudonymisation**: Converts identifier values to stable keyed-hash tokens for use within the system

## Redaction Classes

The redaction system recognizes and removes nine identifier classes:

### 1. National Health Number (Medicare)
**Format**: 10 digits  
**Validation**: Luhn-style checksum with weights [1,3,7,9,1,3,7,9,1,3]  
**Behavior**: Numbers matching the format with valid checksums are redacted; invalid checksums pass through unchanged.

Example:
```
Input:  "Patient Medicare: 1111111113"
Output: "Patient Medicare: [REDACTED]"
```

### 2. Tax Identifier (TFN)
**Format**: 11 digits (optionally hyphenated as XXX-XXX-XXX)  
**Validation**: Weighted sum modulo 89 (checksum must be 0 or 1)  
**Behavior**: Numbers matching the format with valid checksums are redacted; invalid checksums pass through unchanged.

Example:
```
Input:  "TFN: 12 345 678 901"
Output: "TFN: [REDACTED]"
```

### 3. Phone Number
**Format**: Australian phone numbers (02-07 area codes, 04 mobile prefix)  
**Validation**: No checksum (pattern-based)  
**Behavior**: All matching phone numbers are redacted.

Examples:
```
0412345678, +61412345678, (02)12345678
```

### 4. Email Address
**Format**: Standard email (local@domain.tld)  
**Validation**: No checksum (pattern-based)  
**Behavior**: All matching email addresses are redacted.

Example:
```
Input:  "Contact: john.doe@example.com"
Output: "Contact: [REDACTED]"
```

### 5. Date of Birth
**Format**: DDMMYYYY, DD/MM/YYYY, DD-MM-YYYY, YYYYMMDD, YYYY/MM/DD  
**Validation**: No checksum (pattern-based)  
**Behavior**: All matching dates are redacted.

Example:
```
Input:  "Born 15121990"
Output: "Born [REDACTED]"
```

### 6. Street Address
**Format**: Numeric street number followed by street name  
**Validation**: Pattern matching (number + known street type keywords)  
**Behavior**: Street numbers and name tokens are redacted.

Example:
```
Input:  "42 Elm Street, Springfield"
Output: "[REDACTED] [REDACTED], Springfield"
```

### 7. NZ Health Index (NHI)
**Format**: 7 digits + letter (e.g., 1234567A)  
**Validation**: Format validation  
**Behavior**: Matching codes are redacted.

Example:
```
Input:  "NHI: 1234567A"
Output: "NHI: [REDACTED]"
```

### 8. UK Health Number (NHS)
**Format**: 10 digits  
**Validation**: NHS checksum algorithm  
**Behavior**: Numbers matching the format with valid checksums are redacted.

Example:
```
Input:  "NHS: 1234567890"
Output: "NHS: [REDACTED]"
```

### 9. Synthetic Roster Name Matcher
**Format**: Given names and family names from the synthetic roster  
**Validation**: Whole-word matching against roster list  
**Behavior**: Roster names are redacted; common words not on the roster pass through unchanged.

Examples:
```
Input:  "Patient John Smith"
Output: "Patient [REDACTED] [REDACTED]"

Input:  "This is a common case"
Output: "This is a common case"  # "common" not on roster
```

## Redaction Algorithm

### Checksum Validation

For identifier classes with checksums (Medicare, TFN, NHI, NHS), the redaction process is:
1. Match the pattern (e.g., 10 consecutive digits)
2. Extract the candidate (remove formatting)
3. Validate the checksum
4. **If valid**: Replace with `[REDACTED]`
5. **If invalid**: Leave unchanged

This ensures that strings accidentally matching the pattern but with invalid checksums (and thus not real identifiers) are not redacted.

### Pattern Order

Redaction patterns are applied in order:
1. Medicare (10-digit pattern)
2. TFN (11-digit pattern)
3. Phone (country and area code patterns)
4. Email (domain pattern)
5. Date of birth (date patterns)
6. Street address (number + name pattern)
7. NHI (7-digit + letter pattern)
8. NHS (10-digit pattern with checksum)
9. Roster names (word list)

Note: Pattern order can affect results when patterns overlap (e.g., Medicare and NHS both match 10 digits). The system relies on checksum validation to disambiguate these cases.

## Jurisdiction-Independent Redaction

Redaction runs regardless of jurisdiction setting. The same redaction rules apply in AU, UK, and NZ contexts. Jurisdiction-specific variations are handled through rule configuration, not redaction logic.

## Pseudonymisation

### Overview

Pseudonymisation converts raw identifier values to stable keyed-hash tokens. Each token is unique to a combination of (value, key) and stable within a run:
- `pseudonymise(value, key_a)` always produces the same token
- `pseudonymise(value, key_b)` produces a different token (different key)

### Run Key Generation

```python
from clinicloop.compliance.pseudonymise import current_run_key, pseudonymise

# Get a new run key
key = current_run_key()

# Pseudonymise a value
token = pseudonymise("patient_id_123", key)
# Returns: "[PSN-ABCD1234EFGH5678]" or similar

# Same value + same key = same token
token_2 = pseudonymise("patient_id_123", key)
assert token == token_2
```

### Key Lifetime

- **Generation**: One key per invocation of `current_run_key()`; keys differ across invocations
- **Persistence**: Keys are never written to disk (no .env, config, or checkpoint files)
- **Lifetime**: Keys exist only in process memory and are discarded when the process exits

### Token Format

Tokens are designed to be:
- **Opaque**: No part of the original value is recoverable
- **Stable**: Deterministic for a given (value, key) pair
- **Unique**: Different keys produce different tokens
- **Safe**: No 4+ character substring of the input value appears in the output

## Ingress Public Surface

The ingress module exports only one function: `process_record(record)`.

```python
from clinicloop.compliance.ingress import process_record

record = {
    "patient_id": "P123",
    "email": "john.doe@example.com",
    "phone": "0412345678",
}

# Redact PII in string fields
processed = process_record(record)
# All string values in processed record have PII redacted
```

### Boundary Rule

Raw identifier values are accessible only within the ingress module. The public API (`process_record`) accepts records and returns processed records with PII redacted. No exported function returns raw identifiers.

### Private Variables

Module-level variables holding raw identifier data (if any) are prefixed with underscore (`_raw_value`) and excluded from `__all__`. This marks them as private and prevents accidental export.

## Usage Pattern

### Complete Example

```python
from clinicloop.compliance.ingress import process_record
from clinicloop.compliance.pseudonymise import pseudonymise, current_run_key

# Get run key at process start
run_key = current_run_key()

# Process incoming records
record = {
    "patient_id": "P123456789",
    "name": "John Smith",
    "email": "john.smith@clinic.local",
    "phone": "0412345678",
    "dob": "15121990",
}

# Redact PII
processed = process_record(record)
# Result: PII removed from string fields

# Pseudonymise an identifier for database storage
pseudonym = pseudonymise(record["patient_id"], run_key)
# Result: "[PSN-ABCD1234EFGH5678]" - stable per key, different per key
```

## Testing

The ingress module includes tests that verify:
1. Public surface matches the declared `__all__`
2. No raw identifiers leak from `process_record()`
3. All PII classes are redacted appropriately
4. Checksum validation works correctly
5. Pseudonymisation is stable per key and differs across keys
6. Run keys are not persisted to disk

See `tests/compliance/test_ingress_surface.py` and related tests for details.
