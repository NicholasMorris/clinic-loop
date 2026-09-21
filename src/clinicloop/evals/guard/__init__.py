"""Guard evaluation: corpus, metrics, and baseline checks."""

from .baseline import (
    AppendOnlyResult,
    GitReader,
    append_only_diff,
    check_append_only,
    git_show,
)
from .corpus_loader import CORPUS_DIR, FAMILIES, MIN_PER_FAMILY, load_cases, manifest_of
from .guard_case import GuardCase, Message

__all__ = [
    "GuardCase",
    "Message",
    "FAMILIES",
    "MIN_PER_FAMILY",
    "CORPUS_DIR",
    "load_cases",
    "manifest_of",
    "AppendOnlyResult",
    "GitReader",
    "append_only_diff",
    "check_append_only",
    "git_show",
]
