# Documentation Deployment

This page describes the process for building and publishing the documentation site to GitHub Pages.

## The make docs-publish Script

The `scripts/docs_publish.sh` script automates the documentation publication process. It:

1. Runs `mkdocs build --strict` to build the MkDocs site from the `docs/` directory
2. Commits the built site to the `gh-pages` branch in the repository
3. Pushes the updated `gh-pages` branch to `origin/gh-pages`

### Invocation

```bash
bash scripts/docs_publish.sh
```

The script should be run from the repository root and assumes the `gh-pages` branch has already been created and pushed to the remote.

## Live Documentation Check

The `scripts/docs_live_check.py` script verifies that the published documentation site is accessible:

```bash
python scripts/docs_live_check.py <URL>
```

The script:
- Makes an HTTP GET request to the provided URL
- Exits with status 0 if the response is HTTP 200 (OK)
- Exits with status 1 if the response is any other status code
- Prints the observed status code to stderr for non-200 responses

### Status Until First Deployment

The live documentation check is **non-required** until the first successful deployment is made. This is because the published site URL cannot return 200 until the site has been published at least once.

After the first successful deployment, the orchestrator will:
1. Run `scripts/docs_live_check.py` against the published site URL
2. Record the result in this page with the date and status code
3. Mark the live-check as required in the gate

### Live Check Record

**Published site URL:** https://github.com/NicholasMorris/clinic-loop/tree/gh-pages

**Live check record:** (To be added by orchestrator after first deployment)

Example format:
```
- [ISO-8601 date] Status 200: Site is accessible
```

## Integration with CI

The `make ci` gate currently does not run the live-check script, as it requires network access and assumes the site has been published. Future versions may integrate this check into the automated gate after the first successful deployment.
