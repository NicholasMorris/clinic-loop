#!/bin/bash
# Check that each PR includes a changelog fragment and documentation update.
# Usage: checks/fragment.sh [--labels LABELS] <diff-file1> [<diff-file2> ...]
#
# Exit codes:
#   0: All requirements met
#   1: Fragment or docs requirement not met
#   0: No files provided (skipped during make ci)

LABELS=""

# Parse optional labels argument
while [[ $# -gt 0 ]]; do
    case "$1" in
        --labels)
            LABELS="$2"
            shift 2
            ;;
        *)
            break
            ;;
    esac
done

DIFF_FILES=("$@")

# If no files provided, skip (this is called without args during make ci)
if [[ ${#DIFF_FILES[@]} -eq 0 ]]; then
    exit 0
fi

# Check for no-changelog label
if [[ "$LABELS" == *"no-changelog"* ]]; then
    exit 0
fi

# Check for changelog fragment
HAS_FRAGMENT=0
for file in "${DIFF_FILES[@]}"; do
    if [[ "$file" =~ ^changes/[0-9]+\.(feat|fix|docs|chore|test)\.md$ ]]; then
        HAS_FRAGMENT=1
        break
    fi
done

# Check for docs
HAS_DOCS=0
for file in "${DIFF_FILES[@]}"; do
    if [[ "$file" =~ ^docs/ ]]; then
        HAS_DOCS=1
        break
    fi
done

# Report missing requirements
MISSING=()
if [[ $HAS_FRAGMENT -eq 0 ]]; then
    MISSING+=("changelog fragment (changes/<issue>.<type>.md)")
fi
if [[ $HAS_DOCS -eq 0 ]]; then
    MISSING+=("documentation update (docs/*)")
fi

if [[ ${#MISSING[@]} -gt 0 ]]; then
    echo "Missing required changes:"
    for item in "${MISSING[@]}"; do
        echo "  - $item"
    done
    exit 1
fi

exit 0
