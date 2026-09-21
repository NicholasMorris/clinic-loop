"""Loader for the guard adversarial corpus."""

from pathlib import Path

from .guard_case import GuardCase

FAMILIES = (
    "obfuscation",
    "homoglyph_zero_width",
    "multilingual",
    "euphemism",
    "brand_vs_generic",
    "prompt_injection",
    "quote_the_product",
)

MIN_PER_FAMILY = 12

# Corpus directory relative to this module
CORPUS_DIR = Path(__file__).resolve().parents[4] / "evals" / "guard" / "corpus"


def load_cases(corpus_dir: Path | None = None) -> list[GuardCase]:
    """Load all guard cases from the corpus directory.

    Args:
        corpus_dir: Path to corpus directory. If None, uses CORPUS_DIR.

    Returns:
        List of all GuardCase objects loaded from *.jsonl files, sorted by case_id.

    Raises:
        ValueError: If any case_id appears more than once in the corpus.
        NotImplementedError: Stub not yet implemented.
    """
    raise NotImplementedError("load_cases stub")


def manifest_of(cases: list[GuardCase]) -> dict[str, str]:
    """Build manifest of case_id -> expected_verdict.

    Args:
        cases: List of GuardCase objects.

    Returns:
        Dictionary mapping case_id to expected_verdict.
    """
    return {case.case_id: case.expected_verdict for case in cases}
