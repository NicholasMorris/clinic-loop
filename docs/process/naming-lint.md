# Naming lint

The naming lint enforces two hard constraints on the repository:

1. **R7**: Never name the operator or any clinic anywhere in the repository, including commit messages, issue text, and generated files.
2. **I6**: Never use the words "fraud", "drug seeker", or "abuse" when referring to integrity signals or review triage, instead using neutral terminology like "review triage" or "integrity signals".

Both are easy to breach by accident in commit messages, generated diagrams, recorded cassettes, or issue text. Git history is permanent, so a breach cannot be quietly removed later.

## Design

The denylist itself is sensitive: writing forbidden names into a tracked file defeats the purpose of the rule. Therefore:

1. **Hashed storage**: Forbidden names are stored as SHA-256 hashes in `src/clinicloop/naminglint/denylist_hashes.txt` (tracked), never as plaintext.
2. **Single I6 word file**: The I6 word list lives in exactly one tracked file: `src/clinicloop/naminglint/i6_words.txt`. This one occurrence is deliberate and documented.
3. **Out-of-repo plaintext**: The plaintext denylist (operator name, clinic names) lives outside the repository at `$XDG_CONFIG_HOME/clinicloop/naming-denylist.txt` or `$CLINICLOOP_NAMING_DENYLIST`, provisioned by the orchestrator.

## N-gram hashing

The scanner applies NFKC normalization and lowercasing to each line, then forms all whitespace-delimited token n-grams of length 1 to 4 and SHA-256 hashes each. For example, "my clinic name" produces hashes for:

- "my" (1-token)
- "clinic" (1-token)
- "name" (1-token)
- "my clinic" (2-token)
- "clinic name" (2-token)
- "my clinic name" (3-token)

This allows detection even if the name appears as part of a sentence, without needing to commit the name itself.

## I6 words

I6 words are matched case-insensitively and as whole words only in prose:

- "Fraud" and "fraud" both match
- "fraudulent" does NOT match (substring only)
- "drug seeker" is two words and matches the phrase "drug seeker" (with space)

## Exemptions

The following paths are exempt from scanning:

- `src/clinicloop/naminglint/i6_words.txt` — The single tracked I6 word list
- `src/clinicloop/compliance/rules/**` — Guard blocklist terms used in compliance configuration
- `tests/compliance/data/**` — Test data that may contain blocklist terms
- `tests/naminglint/` — Test files that intentionally contain I6 words

## Content kinds scanned

The lint scans:

1. **Tracked source files**: `.py`, `.md`, `.yaml`, `.yml`, `.txt` (via `git ls-files`)
2. **Cassette files**: `*.cassette.json` (recorded LLM and API responses)
3. **Diagram files**: `*.mermaid` (generated state machine diagrams)
4. **Results files**: `*.results.json` (evaluation results and attestations)
5. **Payload files**: Commit messages and PR/issue text (via separate entry point)

## Setup and provisioning

### For clean checkouts (CI)

1. The orchestrator provisions the plaintext denylist at `$XDG_CONFIG_HOME/clinicloop/naming-denylist.txt`.
2. Run the hashing command once before tests:

```bash
python -m clinicloop.naminglint.hash_names
```

This writes hashes to `src/clinicloop/naminglint/denylist_hashes.txt` (tracked).

### For local development

Set the `CLINICLOOP_NAMING_DENYLIST` environment variable to override the default location:

```bash
export CLINICLOOP_NAMING_DENYLIST=/path/to/your/denylist.txt
python -m clinicloop.naminglint.hash_names
```

Then run the lint:

```bash
python -m clinicloop.naminglint.lint --tree
```

### Pre-commit hook

The pre-commit hook is configured in `.pre-commit-config.yaml`:

```yaml
- repo: local
  hooks:
    - id: naming-lint
      name: Naming lint (I6, R7)
      entry: python -m clinicloop.naminglint.lint
      language: system
```

## Error handling

### Empty or missing denylist

`load_denylist()` exits with code 2 and a message if:

- `src/clinicloop/naminglint/denylist_hashes.txt` is missing
- `src/clinicloop/naminglint/denylist_hashes.txt` is empty

This ensures the lint never passes silently with an unconfigured denylist.

### Plaintext not provisioned

Tests that require the plaintext denylist source skip with the reason "plaintext denylist not provisioned". A clean checkout without the plaintext source will skip these tests but still run all other tests.

## CLI usage

### Scan the tree

```bash
python -m clinicloop.naminglint.lint --tree
# or (default)
python -m clinicloop.naminglint.lint
```

Exit code: 0 if no violations, 1 if violations found, 2 if configuration error.

### Scan a payload file

```bash
python -m clinicloop.naminglint.lint --payload commit-message.txt
```

Useful for pre-commit hooks and CI pipelines to scan commit messages and PR text without a full tree scan.

### Hash plaintext denylist

```bash
python -m clinicloop.naminglint.hash_names
```

Reads from `$CLINICLOOP_NAMING_DENYLIST` or `$XDG_CONFIG_HOME/clinicloop/naming-denylist.txt` and writes hashes to `src/clinicloop/naminglint/denylist_hashes.txt`.

## Testing

Conformance tests verify:

- **test_R7.py**: No forbidden hashed names in the tracked tree
- **test_I6.py**: No I6 words outside exempt paths

Both tests run as part of `make ci`.

## References

- Requirement I6: [brief-checklist.md](../brief-checklist.md#I6)
- Requirement R7: [brief-checklist.md](../brief-checklist.md#R7)
