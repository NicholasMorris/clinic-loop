# Changelog Fragments

This directory contains towncrier fragments, one per issue or fix.

## Fragment naming

Fragments are named `<issue-number>.<type>.md`, where:

- `<issue-number>` is the GitHub issue number
- `<type>` is one of: `feat`, `fix`, `docs`, `chore`, `test`

## Fragment types

- **feat** - New feature or enhancement
- **fix** - Bug fix or correction
- **docs** - Documentation-only changes
- **chore** - Maintenance, dependency updates, refactoring
- **test** - Test additions or improvements

## Example

```markdown
# changes/42.feat.md
Added new authentication module with OAuth2 support.
```

## Rendering

Run `towncrier --draft` to preview the changelog, or `towncrier build` to render and consume fragments.

## no-changelog label

A PR with the `no-changelog` label does not require a fragment. This is useful for CI/infrastructure-only changes or those that require no user-facing changelog entry.
