#!/bin/bash
# Guard threshold no-loosening check: exits 0 if no loosening, 1 if loosened.

set -e

# Check if origin/main exists; exit 0 if not (first baseline)
if ! git rev-parse --verify origin/main > /dev/null 2>&1; then
    echo "✓ First baseline: origin/main not yet established"
    exit 0
fi

# Run the no-loosening check
echo "Checking guard threshold no-loosening..."
if ! uv run --locked --extra dev --extra docs --extra sim --extra api --extra agents \
    python -m clinicloop.evals.core.thresholds origin/main HEAD; then
    echo "✗ Threshold loosening detected"
    exit 1
fi

# Run the append-only check
echo "Checking guard corpus append-only..."
if ! uv run --locked --extra dev --extra docs --extra sim --extra api --extra agents \
    python -m clinicloop.evals.guard.baseline; then
    echo "✗ Corpus append-only violation detected"
    exit 1
fi

echo "✓ All checks passed"
exit 0
