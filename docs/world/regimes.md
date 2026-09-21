# SimClinic Regime Parameters

## Overview

Regime parameters are jurisdiction-specific settings that govern SimClinic behavior. Each regime (AU, NZ, UK) defines operational parameters such as shipping costs, SLAs, and consultation requirements.

The regime system is designed to support grounding in real-world operator policies. AU is fully populated. NZ and UK are placeholder regimes that raise `RegimeParameterNotSet` when accessed, signaling that they require implementation.

## Regime Registry

Access regimes using the `get_regime(regime_key)` function:

```python
from clinicloop.world.regimes import get_regime

au = get_regime("au")  # Populated regime
nz = get_regime("nz")  # Placeholder regime
uk = get_regime("uk")  # Placeholder regime
```

The registry contains exactly three keys: `au`, `nz`, `uk`.

## AU Regime (Australia)

**Status:** Populated

**Parameters:**

| Parameter | Value | Inventory ID | Meaning |
|-----------|-------|--------------|---------|
| `flat_shipping_cents` | 995 | po-01 | $9.95 flat shipping fee |
| `free_shipping_threshold_cents` | 12900 | po-01 | Free shipping above $129.00 |
| `termination_cutoff_business_days` | 2 | ps-03 | 2 business days to cancel after placement |
| `damage_report_window_days` | 3 | ps-04 | 3 calendar days to report damage |
| `consultation_validity_months` | 6 | po-02 | Consultation valid for 6 months |
| `delivery_working_days` | (4, 5) | po-06 | Delivery in 4–5 working days |
| `dispatch_commitment_business_days` | 1 | po-02 | Dispatch within 1 business day |

**Recorded Conflicts:**

The AU regime records one documented conflict from the grounded inventory:

- **Inventory ID:** `x-01`
- **Parameter:** Delivery time
- **Documented values:** (4, 5) working days vs. (2, 5) business days
- **Status:** Both values are recorded; AU uses (4, 5) working days as primary

This conflict represents a discrepancy discovered in the source operator's documentation where different pages stated different delivery timelines. Recording the conflict preserves the evidence rather than silently choosing one value.

## NZ Regime (New Zealand)

**Status:** Placeholder

NZ is a placeholder regime. Accessing any parameter raises `RegimeParameterNotSet`:

```python
nz = get_regime("nz")
try:
    value = nz.flat_shipping_cents
except RegimeParameterNotSet as e:
    print(f"Error: {e}")
    # Output: Parameter 'flat_shipping_cents' is not set for regime 'nz' (status: placeholder)
```

**Message Format:**

`RegimeParameterNotSet` exceptions include:
1. The parameter name that was requested
2. The regime key (nz)
3. The status indicator (placeholder)

This design prevents silent fallback to AU values and makes placeholder regimes explicit in error messages.

## UK Regime (United Kingdom)

**Status:** Placeholder

UK is a placeholder regime with the same behavior as NZ. Accessing any parameter raises `RegimeParameterNotSet`.

## Inventory ID Manifest

The `KNOWN_INVENTORY_IDS` frozenset contains all inventory IDs referenced by regime parameters and recorded conflicts:

```python
from clinicloop.world.regimes import KNOWN_INVENTORY_IDS

print(KNOWN_INVENTORY_IDS)
# frozenset({'ps-03', 'ps-04', 'po-01', 'po-02', 'po-06', 'x-01'})
```

**ID Format:** `(ps|cp|po|x)-[0-9]{2}` (two letters, hyphen, two digits)

**Categories:**
- `ps-*` — Patient Support (e.g., termination, damage report)
- `cp-*` — Clinical Process
- `po-*` — Patient Operations (shipping, dispatch)
- `x-*` — Special/Conflict markers (e.g., x-01 for delivery-time conflict)

### Hand Transcription Verification

`KNOWN_INVENTORY_IDS` is **hand-transcribed** from `docs/problem-inventory.md`. It is not machine-checked against that document. Instead:

1. The list is transcribed manually by the developer
2. The orchestrator verifies the transcription against `docs/problem-inventory.md` during PR review
3. The transcription is deliberately not machine-checked because `docs/problem-inventory.md` is published after this issue merges

This approach ensures the inventory is grounded in documented operator policies while allowing the problem inventory to be reviewed and published as a standalone reference document.

## Parameter Object Structure

Every parameter in a populated regime carries:

1. **Value:** The actual parameter value (int, tuple, str, etc.)
2. **Inventory IDs:** A tuple of one or more inventory IDs this parameter cites
3. **Validation:** All IDs are validated against `KNOWN_INVENTORY_IDS`

Example (from AU):

```python
au = get_regime("au")
# delivery_working_days parameter:
#   value: (4, 5)
#   inventory_ids: ('po-06',)
```

## Future Work

Placeholder regimes (NZ, UK) will be populated in future issues by:

1. Researching operator policies for each jurisdiction
2. Documenting findings in the problem inventory
3. Adding parameters to the regime objects
4. Verifying all parameters cite valid inventory IDs
5. Recording any conflicts discovered during research

No default population profile is chosen; `generate_world()` requires explicit `seed`, `population_size`, and `span_days` arguments.
