# Checks

Per-component check scripts discovered and run by `make ci`.

## Discovery contract

The `make ci` target discovers and executes every executable file matching `checks/*.sh` in lexical filename order. Each check script:

- Receives arguments as needed (e.g., diff file lists)
- Exits 0 on success, non-zero on failure
- The first check that exits non-zero causes `make ci` to exit with that status

## Ownership

Each check script is owned by the issue that adds it. The `fragment.sh` check is owned by M0-1 (scaffolder). Later issues add their own checks under `checks/`, with non-overlapping ownership per filename.

## Checks

- `fragment.sh` - Validates that each PR includes a changelog fragment and documentation update (M0-1)
