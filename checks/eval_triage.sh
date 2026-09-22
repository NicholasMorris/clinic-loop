#!/bin/bash
# Triage evaluation gate: recompute artifacts and verify thresholds.

set -e

# Check if origin/main exists; exit 0 if not (first baseline)
if ! git rev-parse --verify origin/main > /dev/null 2>&1; then
    echo "✓ First baseline: origin/main not yet established"
    exit 0
fi

# Run recompute step (uses committed artifacts for CI)
echo "Recomputing triage evaluation..."
if ! uv run --locked --extra dev --extra docs --extra sim --extra api --extra agents \
    python -m evals.triage.recompute; then
    echo "✗ Recompute failed"
    exit 1
fi

# Run gate against committed artifacts
echo "Running triage evaluation gate..."
ARTIFACTS_DIR="evals/results/triage/6742b288454764b8e9934ce1948a22258e7ba7e01228a3e2c45ce61b2749b51e"
if ! uv run --locked --extra dev --extra docs --extra sim --extra api --extra agents \
    python -m evals.triage.gate; then
    echo "✗ Gate check failed"
    exit 1
fi

echo "✓ All checks passed"
exit 0
