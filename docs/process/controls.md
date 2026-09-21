# Process Control Scripts

Five executable scripts enforce rules that are otherwise prose commitments, making the process verifiable and drift-proof. Three scripts are implemented in M0-3; two (merge-precondition checker and review-status poster) are deferred to later milestones.

## Implemented Scripts

### tdd_check

**Purpose:** Verify that a commit follows test-first discipline.

**Invocation:**
```bash
scripts/process/tdd_check.py <repo_path> <commit_sha>
```

**What it checks:**
1. The commit adds at least one file under a `tests/` path
2. The added tests fail (non-zero exit from pytest)
3. Tests fail for one of exactly two accepted reasons:
   - AssertionError from a test
   - NotImplementedError raised from a stub under `src/`

**Exit codes:**
- **0:** Red commit is valid (tests fail for accepted reasons)
- **1:** Red commit is invalid:
  - No test files added in the commit
  - Tests pass (should fail for red commit)
  - Tests fail for wrong reason (collection error, ImportError, SyntaxError, NameError, or AttributeError)

**Accepted failure reasons:**
- AssertionError: Test assertion fails (e.g., `assert False`)
- NotImplementedError: Raised from a stub under `src/` (e.g., `raise NotImplementedError("stub")`)

**Rejected failure reasons:**
- Pytest collection error (SyntaxError in test files)
- ImportError: Missing imports in test or implementation
- SyntaxError: Invalid Python syntax
- NameError: Undefined variables or names
- AttributeError: Accessing non-existent attributes

**Rationale:** Collection errors and import errors mean the test never reached the actual test assertion; they prevent the test from ever running. Name and attribute errors are runtime exceptions that should be caught during development, not hidden by the test framework.

---

### dispatch

**Purpose:** Prevent parallel issues from claiming overlapping file ownership.

**Invocation:**
```bash
echo '[{"key": "M0-1", "files": ["src/..."]}, {"key": "M0-2", "files": ["tests/..."]}]' | scripts/process/dispatch.py
```

**Input format (JSON):**
```json
[
  {
    "key": "M0-1",
    "files": ["src/clinicloop/world/**", "tests/world/"]
  },
  {
    "key": "M0-2",
    "files": ["src/clinicloop/api/**"]
  }
]
```

**What it checks:**
1. No two issues declare overlapping file glob patterns
2. Special rule for `checks/` directory: per-file ownership is disjoint
   - `checks/a.sh` and `checks/b.sh` do not conflict
   - `checks/**` conflicts with all `checks/` files (and vice versa)
3. All other directories follow strict hierarchical overlap detection

**Exit codes:**
- **0:** All issues have disjoint file ownership
- **1:** Two or more issues have overlapping globs (output names the conflicting keys)

**Glob intersection rules:**
- `src/clinicloop/world/**` and `src/clinicloop/world/generator.py` → conflict
- `src/clinicloop/world/**` and `src/clinicloop/api/**` → no conflict
- `checks/a.sh` and `checks/b.sh` → no conflict (per-file ownership in checks/)
- `checks/a.sh` and `checks/**` → conflict

**Rationale:** Without this check, two parallel issues can silently collide when rebased onto main, causing merge conflicts or accidentally overwriting each other's work.

---

### post_merge_sync

**Purpose:** Verify local checkout matches the remote after a merge.

**Invocation:**
```bash
echo '{"local_head_sha": "abc123", "remote_head_sha": "abc123", "working_tree_dirty": false}' | scripts/process/post_merge_sync.py
```

**Input format (JSON):**
```json
{
  "local_head_sha": "abc123def456...",
  "remote_head_sha": "abc123def456...",
  "working_tree_dirty": false
}
```

**What it checks:**
1. Local HEAD SHA matches the recorded remote default-branch SHA
2. Working tree is clean (no uncommitted changes)

**Exit codes:**
- **0:** Local matches remote and tree is clean
- **1:** Divergent HEAD or dirty tree (output names which condition failed)

**Rationale:** After merging a PR to main, the orchestrator should verify that:
- The local checkout was fast-forwarded (not rebased or pushed with divergence)
- No uncommitted changes remain (e.g., from a failed CI cleanup)

---

## Deferred Scripts

### Merge-precondition checker (deferred to M0-4+)
Would read GitHub status-rollup payloads and verify that all required status contexts have completed with SUCCESS, with the citation job (report-only) allowed to be SKIPPED.

### Review-status poster (deferred to M0-4+)
Would post one commit-status context per review persona (correctness, security, regulatory, test-quality, docs), reading names from `scripts/repo_settings/review_contexts.py`.

---

## Status Context Registry

**Defined contexts** (in `scripts/repo_settings/review_contexts.py`):
```python
REQUIRED_STATUS_CONTEXTS = (
    "local-ci",           # Posted by post_gate_status.py after make ci passes
    "correctness",        # Posted by review persona (deferred)
    "security-privacy",   # Posted by review persona (deferred)
    "regulatory-guard",   # Posted by review persona (deferred)
    "test-quality",       # Posted by review persona (deferred)
    "docs",               # Posted by review persona (deferred)
)
```

**Skip allow-list:**
- Currently empty (only citation job is implicitly skipped; citation checker is deferred)
- Growing the allow-list is a sequenced edit to the merge-precondition checker script (M0-4+), never a change made by a new job's own issue

---

## Network Isolation

All scripts in this module operate without opening sockets. They read:
- Filesystem: commit diffs via `git` (local operations only)
- JSON payloads: stdin or file paths provided by the orchestrator
- No GitHub API calls: credentials and tokens are held by the orchestrator only

This design allows subagents to run scripts against fixture payloads in CI without network access or credentials.

---

## See Also

- **Issue M0-3:** Defines AC1–AC7 for this milestone (P1, P2, P5 covered here; P3, P6 deferred)
- **Requirement IDs:** P1 (dispatch), P2 (tdd_check), P5 (post_merge_sync)
- **PR template:** Links to the first commit's SHA so reviewers can verify the red commit
