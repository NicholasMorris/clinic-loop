# Evaluation Core Framework

This document describes the core evaluation infrastructure that enables consistent metric tracking, baseline comparison, and conformance testing across all components.

## Registry

The **metric registry** enables components to register named metrics with threshold values. Each component owns a global registry entry for its metrics, preventing duplicate registrations.

```python
from clinicloop.evals.core.registry import register_metric, DuplicateMetric

def accuracy_metric(predictions, ground_truth):
    return sum(p == g for p, g in zip(predictions, ground_truth)) / len(predictions)

# Register the metric
register_metric("triage", "intent_accuracy", accuracy_metric, threshold=0.95)

# Duplicate registration raises DuplicateMetric
register_metric("triage", "intent_accuracy", accuracy_metric, threshold=0.95)  # raises
```

## Per-Case Artifacts

Every evaluation run produces **per-case artifacts**—JSON files capturing the inputs, outputs, and metadata for a single test case. These artifacts are stored under `evals/results/<component>/<tree-hash>/` in a Pydantic schema:

```python
from clinicloop.evals.core.artifacts import CaseArtifact, write_case

artifact = CaseArtifact(
    case_id="test_001",
    component="triage",
    tree_hash="abc123def456...",
    seed=42,
    outputs={"intent": "urgent", "confidence": 0.98}
)

write_case(Path("evals/results/triage/abc123def456.../test_001.json"), artifact)
```

### Schema

- **case_id** (str): Unique identifier for this test case
- **component** (str): Component being evaluated (e.g., "triage", "integrity", "consult")
- **tree_hash** (str): SHA256 hash of eval-relevant paths (see below)
- **seed** (int): Random seed for reproducibility
- **outputs** (dict): Component-specific output data

### Append-Only Rule

Once written, a case file cannot be overwritten. Attempting to do so raises `AppendOnlyViolation`:

```python
from clinicloop.evals.core.artifacts import AppendOnlyViolation

write_case(path, artifact1)  # Success
write_case(path, artifact2)  # Raises AppendOnlyViolation
```

## Tree Hash and Eval-Relevant Paths

The **tree hash** is a SHA256 digest of the source code that was evaluated. It is computed from a list of paths in `evals/eval-relevant-paths.txt`:

```
src/clinicloop/evals/core
tests/evals/core
```

For each path, the tree hash captures the blob SHA at `HEAD:<path>` in git, then hashes the newline-joined, sorted lines:

```
path1 abc123def456...
path2 def456abc123...
```

The tree hash is recomputed whenever any listed path changes, making it easy to detect staleness:

```python
from clinicloop.evals.core.artifacts import compute_tree_hash

tree_hash = compute_tree_hash(Path("evals/eval-relevant-paths.txt"))
```

## Recompute and Staleness Detection

The **recompute script** validates that committed aggregate results match the values computed from per-case artifacts:

```python
from clinicloop.evals.core.recompute import recompute

exit_code = recompute(Path("evals/results/triage"))
```

Returns:
- **0** if all aggregates match and tree hashes are current
- **1** if any aggregate differs or tree hash is stale

This ensures that metrics in `README.md` or reports are always consistent with the source data.

## Thresholds and No-Loosening Check

Each component stores its metric thresholds in `evals/<component>/thresholds.toml`:

```toml
[metrics]
intent_accuracy = { threshold = 0.95, direction = "higher" }
escalation_recall = { threshold = 1.0, direction = "higher" }
```

The **no-loosening check** compares thresholds on the current branch against those on `origin/main`, failing if any threshold becomes more permissive:

```python
from clinicloop.evals.core.thresholds import check_no_loosening

# For higher-is-better: threshold is loosened if head < base
# For lower-is-better: threshold is loosened if head > base
exit_code = check_no_loosening("origin/main", "HEAD")
```

Returns:
- **0** if thresholds are equal or stricter
- **1** if any threshold is loosened

Threshold and result changes reach `main` only through a PR with the `baseline-change` label, allowing reviewers to explicitly approve metric relaxations.

## Cassettes

**Cassettes** store recorded LLM responses keyed by a four-tuple:

```python
from clinicloop.evals.core.cassettes import cassette_key, lookup, record

key = cassette_key(
    model_id="unsloth/Qwen3-30B-A3B-Instruct-2507-GGUF",
    prompt_hash="abc123def456...",
    sample_index=0,
    seed=42
)

# Record a response
record(key, {"text": "The answer is 42", "tokens": 15})

# Look up a response
response = lookup(key)
```

The **sample index** is included in the key, so different samples of the same prompt produce different responses:

```python
key1 = cassette_key(model_id, prompt_hash, sample_index=0, seed=42)
key2 = cassette_key(model_id, prompt_hash, sample_index=1, seed=42)
assert key1 != key2  # Different samples
```

## Requirement Coverage and Conformance

The conformance system maps requirement identifiers to tests via pytest markers. Each test function is marked with `@pytest.mark.checklist_id("<ID>")`:

```python
@pytest.mark.checklist_id("E2")
def test_registry_prevents_duplicates():
    """AC1: Registering duplicate metrics raises DuplicateMetric."""
    # Test body
```

The conformance module scans all tests and reports unmapped requirements:

```python
from clinicloop.evals.core.conformance import unmapped_requirement_ids, load_expected_unmapped

unmapped = unmapped_requirement_ids(Path("docs/brief-checklist.md"))
expected = load_expected_unmapped(Path("tests/conformance/expected_unmapped.txt"))

assert unmapped == expected, "Unmapped requirements don't match allowlist"
```

### Expected Unmapped Allowlist

`tests/conformance/expected_unmapped.txt` lists requirement IDs that are intentionally not yet tested:

```
E1  # Retired by M2-6, M3-4, M5-6, M6-7, M7-1
B2
C0
C1
C2
C3
C4
...
```

Entries with inline comments explain which issues will retire them. If a new requirement is added without a test, or if an allowlist entry is removed but its test still doesn't exist, the conformance check fails the build.

## Integration with CI

The local gate (`make ci`) runs:

1. **Linting** (ruff)
2. **Type checking** (mypy strict)
3. **Unit tests** (pytest, excluding `local_model` marker)
4. **Conformance** (requirement coverage check)

Each component's own workflow (e.g., `checks/eval_triage.sh`) is discovered and executed, allowing component owners to define custom gates without editing the central gate script.
