# Checks

Per-component check scripts discovered and run by `make ci`.

## Discovery contract

After ruff, mypy and pytest, `make ci` runs every executable file matching `checks/*.sh` in lexical filename order. Nothing lists them: adding a file adds a check, with no edit to the Makefile.

- A check exits 0 on success and non-zero on failure.
- The first check that exits non-zero fails `make ci`, and later checks do not run.
- Files that are not executable are skipped.

## Ownership

Each check script is owned by the issue that adds it. `fragment.sh` is owned by M0-1. Later issues add their own files here and never edit another issue's file, so ownership never overlaps.

## Checks

- `fragment.sh` - the P4 mechanism. Given the names changed against the merge base as arguments, it requires a changelog fragment named `changes/<issue-number>.<type>.md` (type feat, fix, docs, chore or test) and a path under `docs/`, and names each unmet requirement. `--labels bug,no-changelog` waives both. With no arguments it reports that it was skipped.
