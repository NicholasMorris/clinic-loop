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
    """
    if corpus_dir is None:
        corpus_dir = CORPUS_DIR

    import json

    cases = []
    case_ids_seen = set()

    # Load all *.jsonl files in sorted order
    jsonl_files = sorted(corpus_dir.glob("*.jsonl"))

    for jsonl_path in jsonl_files:
        with open(jsonl_path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.rstrip("\n")
                if not line or line.startswith("#"):
                    continue

                obj = json.loads(line)
                case = GuardCase.model_validate(obj)

                # Check for duplicate case_id
                if case.case_id in case_ids_seen:
                    msg = f"Duplicate case_id: {case.case_id!r} in {jsonl_path}"
                    raise ValueError(msg)
                case_ids_seen.add(case.case_id)

                cases.append(case)

    # Sort by case_id for stable ordering
    cases.sort(key=lambda c: c.case_id)

    return cases


def manifest_of(cases: list[GuardCase]) -> dict[str, str]:
    """Build manifest of case_id -> expected_verdict.

    Args:
        cases: List of GuardCase objects.

    Returns:
        Dictionary mapping case_id to expected_verdict.
    """
    return {case.case_id: case.expected_verdict for case in cases}
