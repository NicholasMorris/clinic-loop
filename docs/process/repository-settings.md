# Repository Settings

This page documents the expected configuration for the clinic-loop repository.

## Repository Settings

The repository must be configured as follows:

- **Repository name:** clinic-loop
- **Repository visibility:** public
- **Default branch:** main

## GitHub Pages Configuration

GitHub Pages must be enabled with the following settings:

- **Build type:** legacy (built and deployed from a branch)
- **Source branch:** gh-pages

## Branch Protection

The default branch (main) must have protection rules that require the following status checks to pass before merging:

- local-ci
- correctness
- security-privacy
- regulatory-guard
- test-quality
- docs

## Token Scopes

The repository token must have the following OAuth scopes:

- repo
- read:org

The `repo` scope allows repository creation, branch protection, Pages configuration, and commit status updates. The `read:org` scope allows resolving the owning account.

## Running the Checker

The `scripts/repo_settings/check.py` module provides three checker functions:

### check_settings(payload_path)

Verifies repository settings by checking a GitHub API repository payload.

### check_protection(payload_path)

Verifies branch protection settings by checking a GitHub API branch protection payload.

### check_token_scopes(payload_path)

Verifies token scopes by checking the X-OAuth-Scopes header from API responses.

Each function accepts a file path or reads from standard input if no path is provided.
