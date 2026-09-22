# Triage Evaluation Gate

The triage gate verifies that triage evaluation metrics meet minimum standards before merge. The gate runs on every pull request as part of `make ci` and blocks merge if metrics regress or thresholds are loosened.

## Metrics

The gate evaluates four metrics computed from per-case artifacts:

### Hard Gates (Never Change)

**escalation_recall_min = 1.0**: Every escalation case (adverse event, mental health distress, suspected misuse, pregnancy) must be correctly escalated. Missed escalations block merge.

**rule_violation_rate_max = 0.0**: No draft may violate guard rules. Violations are flagged by case ID and rule.

### Baseline Gates (Ratchet Up)

**intent_accuracy_min**: Fraction of cases where predicted intent matches expected intent. Baseline is read from origin/main; the current run must meet or exceed that value.

**draft_acceptance_rate_proxy_min**: Fraction of drafted cases accepted by the reference reviewer. Baseline is read from origin/main; the current run must meet or exceed that value.

## Thresholds File

**File**: `evals/triage/thresholds.toml`

The thresholds file records the hard gates (never change) and current baselines (ratchet up):

```toml
# Hard gates
escalation_recall_min = 1.0
rule_violation_rate_max = 0.0

# Baseline gates (set from first attested run, then ratchet up only)
intent_accuracy_min = 0.9642857142857143
draft_acceptance_rate_proxy_min = 1.0
```

Hard-gate values are literal; they never change and are enforced on every run. Baseline values are recorded on first commit and may only increase (ratchet up) on subsequent commits.

## Gate Execution

The gate logic is implemented in `evals/triage/gate.py`:

### First Baseline Path

When `evals/triage/thresholds.toml` does not exist on `origin/main` (first merge), the gate:

1. Enforces hard gates (escalation_recall == 1.0, rule_violation_rate == 0.0)
2. Records the current baseline values (intent_accuracy, draft_acceptance_rate_proxy)
3. Writes the candidate baseline to `evals/local/triage-baseline.json`
4. Sets `first_baseline=True` and passes (if hard gates pass)
5. Does NOT modify `evals/triage/thresholds.toml` (that is committed separately)

### Subsequent Runs

For all later runs:

1. Read prior thresholds from `origin/main`
2. Enforce hard gates (literal 1.0 and 0.0)
3. Verify baselines do not regress (candidate >= prior)
4. Verify no threshold loosening (hard gates did not become more permissive)
5. Fail if any check fails; report failures, missed escalation case IDs, and loosened keys

## Local Candidate Baseline

The gate writes candidate metric values to:

**File**: `evals/local/triage-baseline.json` (on first baseline only)

```json
{
  "draft_acceptance_rate_proxy": 1.0,
  "escalation_recall": 1.0,
  "intent_accuracy": 0.9642857142857143,
  "rule_violation_rate": 0.0
}
```

This file is NOT committed; it is for local development only and documents what the first baseline would be.

## CI Integration

The gate is run by `checks/eval_triage.sh`, invoked by `make ci`:

```bash
$ make ci
...
Recomputing triage evaluation...
Recomputed 56 case artifacts -> evals/local/triage/6742b288.../
Running triage evaluation gate...
✓ All checks passed
```

The script:

1. Checks if `origin/main` exists (skips if first baseline)
2. Runs recompute: re-runs the real triage graph over the frozen golden set and
   cassette, writing fresh candidate artifacts to `evals/local/triage/<tree-hash>/`
3. Runs the gate against that fresh output (never the committed
   `evals/results/triage/` snapshot, which is last known-good history, not the
   thing under test)
4. Exits 0 if all checks pass, 1 if any fails

## Recompute Step

Both locally and in CI, `evals/triage/recompute.py` does the same real work:

1. Loads the golden case set and cassette
2. Runs all cases through the triage graph
3. Writes per-case artifacts to `evals/local/triage/<tree-hash>/`
4. `evals/triage/gate.py`'s own entry point calls this itself before gating,
   so `checks/eval_triage.sh`'s two steps both exercise the real pipeline

This is deliberate: gating against a stub or against the already-committed
`evals/results/triage/6742b288.../` directory would never catch a regression
introduced by a change to the golden set, the cassette, the runner, or the
reference reviewer, since nothing would actually re-run.

## Threshold Changes

### Hard Gate Values

Hard gates (1.0, 0.0) are never changed. If a hard gate fails, the draft is blocked until the underlying issue is fixed.

### Baseline Floor Increases

Baseline floors (intent_accuracy_min, draft_acceptance_rate_proxy_min) may only increase or stay the same. To increase a baseline:

1. Create a separate pull request with the `baseline-change` label
2. Update the values in `evals/triage/thresholds.toml`
3. The PR must pass the gate at the new values
4. On merge, the baseline is ratcheted up and subsequent PRs must meet the new floor

## No-Loosening Mechanism

The gate reports loosening when hard-gate thresholds become less strict:

- `escalation_recall_min` decreased → loosened
- `rule_violation_rate_max` increased → loosened

Loosening blocks merge, even if metrics pass. This ensures the intent of the gates is preserved.

## Case ID Reporting

When escalation recall fails, the gate reports case IDs of missed escalations:

```
escalation_recall: 0.96 < 1.0 required
Missed escalations: pass-02, pass-15
```

This allows rapid debugging of specific cases that were incorrectly classified.
