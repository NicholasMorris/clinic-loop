# SimClinic Entity Models

## Overview

SimClinic entities represent the core data structures of the synthetic clinic simulation. All entities are frozen pydantic models with an explicit `synthetic: Literal[True]` field that enforces synthetic-only status. This ensures no real data can be accidentally used in the simulation.

## Entity Types

### Patient

A patient record in the SimClinic system.

**Fields:**
- `synthetic: Literal[True]` — Marker indicating this is synthetic data only
- `phone_number: Optional[str]` — Fictional phone number in range 0400-0499
- `email_domain: Optional[str]` — Fictional email domain (test.example.com)
- `health_identifier: Optional[str]` — Fictional health identifier prefixed with 99

**Constraints:**
- Model is frozen (immutable)
- Cannot be constructed with `synthetic=False`
- Field assignment after construction raises `ValidationError`

### Questionnaire

A patient questionnaire response captured during intake.

**Fields:**
- `synthetic: Literal[True]` — Marker indicating this is synthetic data only

**Constraints:**
- Model is frozen (immutable)

### Consult

A clinical consultation record.

**Fields:**
- `synthetic: Literal[True]` — Marker indicating this is synthetic data only

**Constraints:**
- Model is frozen (immutable)

### Prescription

A prescription issued by a clinician.

**Fields:**
- `synthetic: Literal[True]` — Marker indicating this is synthetic data only

**Constraints:**
- Model is frozen (immutable)

### Order

An order placed for fulfillment (e.g., pharmacy dispatch).

**Fields:**
- `synthetic: Literal[True]` — Marker indicating this is synthetic data only

**Constraints:**
- Model is frozen (immutable)

### Message

A message exchanged between patient and clinic.

**Fields:**
- `synthetic: Literal[True]` — Marker indicating this is synthetic data only

**Constraints:**
- Model is frozen (immutable)

## Fictional Identifier Ranges

All generated identifiers fall within declared fictional ranges to prevent any possibility of collision with real data:

### Phone Numbers

**Range:** 0400-0499 (Australian fictional range)
- Format: `0400-0499` followed by 7-digit number
- Example: `0400` + random 7 digits

### Email Domain

**Value:** `test.example.com`
- Reserved for testing per RFC 6761
- All synthetic emails use this domain

### Health Identifiers

**Prefix:** `99` (fictional prefix unlikely to appear in real IDs)
- Format: `99` + 8-digit number
- Range: 0-99,999,999

## World Snapshot Contract

The world snapshot is a versioned JSON file that captures the parameters used to generate a world. It enables reproducible simulation runs and validation of determinism.

**Schema:**

```json
{
  "schema_version": "1",
  "seed": <int>,
  "population_size": <int>,
  "span_days": <int>,
  "entities": {
    "patients": <int>,
    "questionnaires": <int>,
    "consults": <int>,
    "prescriptions": <int>,
    "orders": <int>,
    "messages": <int>
  }
}
```

**Fields:**
- `schema_version` (string) — Currently "1"; used to support future schema evolution
- `seed` (int) — Random seed used for generation (enables exact reproduction)
- `population_size` (int) — Number of patients generated
- `span_days` (int) — Number of days the simulation spans
- `entities` (object) — Count of each entity type generated

**Determinism Guarantees:**

1. Identical arguments (`seed`, `population_size`, `span_days`) always produce identical snapshots
2. Different seeds produce different snapshots
3. Reading a snapshot file and re-exporting produces an identical SHA-256 digest
4. Results are reproducible across different Python processes with different `PYTHONHASHSEED` values
5. Stream isolation ensures that consuming from one entity stream does not affect others

## Stream Isolation

Each entity type has its own independent `numpy.random.Generator` stream, seeded from a spawned `SeedSequence` derived from the main seed. This design ensures:

1. **Independence:** Changing the generation logic for one entity type does not affect others
2. **Reproducibility:** Exact reproduction is possible across runs and processes
3. **Testability:** Stream isolation can be verified by calling generate_world multiple times
