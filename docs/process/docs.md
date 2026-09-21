# Documentation

This page documents the documentation structure and conventions for ClinicLoop.

## Documentation Site

The ClinicLoop documentation is built with MkDocs Material and published via GitHub Pages.

### Navigation

Navigation is managed through `mkdocs-awesome-nav`. Each directory under `docs/` can include
a `.nav.yml` file that defines the navigation structure for that section. The main navigation
is defined in `docs/.nav.yml`, which uses includes to assemble the full navigation hierarchy.

### Adding New Pages

To add a new page to the documentation:

1. Create a new `.md` file in the appropriate directory under `docs/`
2. Add an entry to the `.nav.yml` file in that directory
3. The page will automatically appear in the navigation without editing the main `mkdocs.yml`

### Architecture Decision Records

All significant architectural decisions are documented as ADRs in the `docs/adr/` directory.
Each ADR follows a standard template with sections for Status, Context, Decision, Consequences,
and Alternatives considered.

See `docs/adr/index.md` for the complete list of ADRs.

## Building the Documentation

Build the documentation locally:

```bash
mkdocs build
```

Serve the documentation for preview:

```bash
mkdocs serve
```

Build in strict mode (fails on any warnings or broken links):

```bash
mkdocs build --strict
```
