"""Repository settings constants for review contexts and token scopes."""

REQUIRED_STATUS_CONTEXTS = (
    "local-ci",
    "correctness",
    "security-privacy",
    "regulatory-guard",
    "test-quality",
    "docs",
)

REQUIRED_TOKEN_SCOPES = (
    "repo",
    "read:org",
)
