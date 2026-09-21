## Issue

Closes #<issue-number>

## Red-commit SHA

<!-- The first commit on the branch: failing tests and stubs only. -->
`<red-commit-sha>`

## Files globs

<!-- The write-allowed globs from the issue that this change touches. -->
- `<glob>`

## Docs and fragment

<!-- Both are required unless the no-changelog label is applied. -->
- Documentation page edited under `docs/`: `docs/<page>.md`
- Changelog fragment: `changes/<issue-number>.<type>.md` (type: feat, fix, docs, chore or test)

## Checklist

- [ ] `make ci` passes
- [ ] Tests were committed red before the implementation
- [ ] Synthetic data only

## Description

<!-- What changed and why. -->
