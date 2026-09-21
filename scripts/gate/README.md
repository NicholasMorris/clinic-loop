# Gate Scripts

This directory contains scripts that implement enforcement gates and checks for the CI pipeline.

## Pre-Push Hook

The `.githooks/pre-push` hook is installed by `make hooks` and runs the local gate (`make ci`) before each push. This ensures all checks pass without needing to push and wait for CI feedback.

## Check Discovery

The `make ci` target discovers and executes all executable shell scripts under `checks/*.sh` in lexical filename order. Each script is responsible for checking a specific aspect of the codebase.

Scripts are added by individual issues and should exit with status 0 for success or non-zero for failure.
