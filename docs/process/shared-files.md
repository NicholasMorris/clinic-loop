# Shared Files and Governance

This document describes the scaffolder-owned shared configuration files and the parallel-issue coordination rules.

## Scaffolder-owned shared files

These files are owned by the scaffolder (M0-1) and cannot be edited by feature branches without coordination:

- **pyproject.toml** - Python package metadata, the complete dependency manifest spread over the extras (sim, api, agents, audio, docs, dev), mypy strict configuration with per-module overrides, ruff configuration with Google-style docstrings, the `clinicloop-doctor` and `clinicloop-install` script entry points, towncrier configuration
- **uv.lock** - Resolved dependency versions, tracked in git and produced with `uv lock --python 3.12`. The manifest names libraries only and pins no versions; the lockfile holds them
- **.python-version** - Python version requirement (3.12)
- **Makefile** - Build automation with `ci`, `doctor`, and `setup` targets. Tools run through `uv run --locked --extra dev`, so a fresh checkout works
- **.gitignore** - Pre-declared ignored paths (data/, runs/, corpus/rendered/, .venv, evals/local/)
- **CODEOWNERS** - Code ownership assignments for gate-critical paths
- **.github/PULL_REQUEST_TEMPLATE.md** - PR template with fields for the red-commit SHA, the files globs and the docs-and-fragment entry
- **src/clinicloop/py.typed** - Empty typing marker shipped as package data

## Gate-critical CODEOWNERS prefixes

Seven prefixes are protected and require CODEOWNERS entries:

1. `scripts/process/**` - Process scripts run by the orchestrator
2. `checks/**` - CI check scripts discovered by `make ci`
3. `src/clinicloop/naminglint/**` - Naming compliance enforcement
4. `src/clinicloop/compliance/**` - Regulatory and guard rules
5. `src/clinicloop/evals/thresholds*` - Evaluation thresholds and baselines
6. `src/clinicloop/agents/integrity/forbidden_features*` - Forbidden feature definitions
7. `docs/process/**` - Process documentation

## Checks discovery contract

The `make ci` target discovers and executes every executable file matching `checks/*.sh` in lexical order:

```makefile
for check in checks/*.sh; do \
    [ -x "$$check" ] || continue; \
    "$$check" || exit $$?; \
done
```

The ruff, mypy and pytest steps run first. The first failing command stops `make ci`. Non-executable files are skipped. `checks/fragment.sh` takes the names changed against the merge base as arguments, plus an optional `--labels` list; called with no arguments, as `make ci` does, it reports that it was skipped.

Each issue that adds a check owns that check file. Files are owned non-overlappingly (no two issues edit the same `.sh` file).

## Per-file ownership inside checks/

Once an issue owns a `checks/foo.sh` file, only that issue edits it. Later issues add new check files, never modify existing ones. This prevents conflicts in `make ci` discovery.

## Fragment types

Towncrier fragments are named `changes/<issue-number>.<type>.md` with exactly five types:

- **feat** - New feature
- **fix** - Bug fix
- **docs** - Documentation-only
- **chore** - Maintenance / refactoring
- **test** - Test improvements

No other types are declared in `pyproject.toml`.

## Pre-declared .gitignore entries

The .gitignore file pre-declares every path the backlog will need to ignore, preventing later conflicts:

- `data/` - Synthetic data and results
- `runs/` - Experiment runs and logs
- `corpus/rendered/` - Rendered audio corpus
- `.venv` - Python virtual environment
- `evals/local/` - Local evaluation results

Beyond these five, only ordinary Python and tooling ignores (`__pycache__/`, `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`, `dist/`, `build/`, `site/` and similar) are listed. `uv.lock` is deliberately not ignored. No other issue may add entries to .gitignore; it is owned by M0-1.

## no-changelog label

A PR with the `no-changelog` label does not require a changelog fragment or a docs edit. The `checks/fragment.sh` script matches the label exactly (`--labels bug,no-changelog`) and exits 0. Without the label it exits 1 and names each unmet requirement (changelog fragment, documentation edit). Use the label for:

- CI/infrastructure-only changes with no user-facing impact
- Process or tooling changes
- Changes to examples or non-production code

## Parallel issue rules

- Dependency manifest conflicts vanish: `pyproject.toml` and `uv.lock` are written once by M0-1
- Changelog conflicts vanish: each issue has its own fragment file `changes/<issue-number>.<type>.md`
- Docs nav conflicts vanish: the docs site uses per-directory `.nav.yml` files, set up in M0-5a and M0-5b
- Checks are discovered, not listed: new checks are added as files, not edited into a centralized list

## Why this matters

Sixty-odd issues run in parallel. Without these rules:

- Every branch would conflict in `pyproject.toml` on merge
- Every branch would conflict in `CHANGELOG.md` after merge
- The CI contract would require someone to manually list every check

These shared files are written once, up front, and never edited again by feature work.
