#!/bin/bash
# Triage evaluation gate: recompute artifacts and verify thresholds.

set -e

# Check if origin/main exists; exit 0 if not (first baseline)
if ! git rev-parse --verify origin/main > /dev/null 2>&1; then
    echo "✓ First baseline: origin/main not yet established"
    exit 0
fi

# Recompute: re-run the real pipeline over the frozen golden set + cassette,
# writing fresh candidate artifacts under evals/local/triage/<tree-hash>/.
echo "Recomputing triage evaluation..."
if ! uv run --locked --extra dev --extra docs --extra sim --extra api --extra agents \
    python -m evals.triage.recompute; then
    echo "✗ Recompute failed"
    exit 1
fi

# Gate: run_gate also re-runs the recompute step itself and gates on its
# FRESH output, never the committed evals/results/ snapshot.
echo "Running triage evaluation gate..."
if ! uv run --locked --extra dev --extra docs --extra sim --extra api --extra agents \
    python -m evals.triage.gate; then
    echo "✗ Gate check failed"
    exit 1
fi

echo "✓ All checks passed"
exit 0
