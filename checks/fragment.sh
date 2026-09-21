#!/bin/bash
# P4 mechanism: every change ships a changelog fragment and a documentation edit.
#
# Usage: checks/fragment.sh [--labels LABEL[,LABEL...]] [PATH ...]
#
# PATH arguments are the names changed against the merge base. Labels are separated by commas
# or whitespace. With no PATH arguments (as when make ci discovers this script) the check is
# skipped, because no diff list was supplied.
#
# Exit status: 0 when both requirements are met, the no-changelog label is present, or the
# check is skipped; 1 when a requirement is unmet, naming each unmet requirement.

labels=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --labels)
            labels="${2:-}"
            shift 2
            ;;
        *)
            break
            ;;
    esac
done

if [[ $# -eq 0 ]]; then
    echo "fragment check skipped: no changed-file list supplied"
    exit 0
fi

for label in ${labels//,/ }; do
    if [[ "$label" == "no-changelog" ]]; then
        echo "fragment check waived by the no-changelog label"
        exit 0
    fi
done

has_fragment=0
has_docs=0
for path in "$@"; do
    if [[ "$path" =~ ^changes/[0-9]+\.(feat|fix|docs|chore|test)\.md$ ]]; then
        has_fragment=1
    fi
    if [[ "$path" == docs/* ]]; then
        has_docs=1
    fi
done

status=0
if [[ $has_fragment -eq 0 ]]; then
    echo "unmet requirement: changelog fragment named changes/<issue-number>.<type>.md" \
        "(type is one of feat, fix, docs, chore, test)"
    status=1
fi
if [[ $has_docs -eq 0 ]]; then
    echo "unmet requirement: documentation edit under docs/"
    status=1
fi
exit $status
