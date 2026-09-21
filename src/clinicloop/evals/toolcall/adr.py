"""Parse and validate the LLM model selection ADR."""

import re
from pathlib import Path
from typing import TypedDict


class ModelRole(TypedDict):
    """Model selection for a given role.

    Attributes:
        model_id: The model identifier.
        pass_count: Number of cases passed out of 30.
        tokens_per_second: Measured generation speed.
        family: The model family (e.g., 'qwen', 'gpt_oss', 'gemma').
    """

    model_id: str
    pass_count: int
    tokens_per_second: float
    family: str


class ModelSelectionADR(TypedDict):
    """Parsed model selection ADR.

    Attributes:
        status: The ADR status (e.g., 'Accepted').
        roles: Dict of role name to ModelRole (primary, judge, fallback).
    """

    status: str
    roles: dict[str, ModelRole]


def parse_model_selection_adr(adr_path: str) -> ModelSelectionADR:
    """Parse the LLM model selection ADR.

    Reads and validates docs/adr/llm-model-selection.md. The ADR must:
    - Have status 'Accepted'
    - Name exactly the roles: primary, judge, fallback
    - Each role carries: pass count, tokens-per-second, family
    - Judge family must differ from primary family
    - Primary pass count >= promotion_bar().primary_min_passing_cases

    Args:
        adr_path: Path to the ADR file (typically docs/adr/llm-model-selection.md).

    Returns:
        A ModelSelectionADR dict with status and roles.

    Raises:
        FileNotFoundError: If the ADR file is not found.
        ValueError: If the ADR is invalid.
    """
    from clinicloop.evals.toolcall.thresholds import promotion_bar

    adr_file = Path(adr_path)
    if not adr_file.exists():
        raise FileNotFoundError(f"ADR file not found: {adr_path}")

    content = adr_file.read_text()

    # Parse status from "## Status" section
    status_match = re.search(r"##\s+Status\s*\n+([^\n]+)", content)
    if not status_match:
        # Fallback to inline "Status: ..." format
        status_match = re.search(r"Status:\s*(\w+)", content)
        if not status_match:
            raise ValueError("ADR missing 'Status' section")
        status = status_match.group(1)
    else:
        status = status_match.group(1).strip()

    # Extract role sections (Primary, Judge, Fallback)
    roles: dict[str, ModelRole] = {}

    # Regex pattern for role sections with model_id, family, pass_count, and tokens_per_second
    role_pattern_template = (
        r"###\s+{role_name}.*?\n"
        r"- \*\*Model ID:\*\*\s+([^\n]+)\n"
        r".*?- \*\*Family:\*\*\s+([^\n]+)\n"
        r".*?- \*\*Measured Pass Count:\*\*\s+(\d+).*?\n"
        r".*?- \*\*Measured Tokens/Second:\*\*\s+([\d.]+)"
    )

    role_patterns = {
        "primary": role_pattern_template.format(role_name="Interim Primary:"),
        "judge": role_pattern_template.format(role_name="Judge:"),
        "fallback": role_pattern_template.format(role_name="Fallback:"),
    }

    for role_name, pattern in role_patterns.items():
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        if not match:
            raise ValueError(f"ADR missing or malformed '{role_name}' role section")

        model_id, family, pass_count, tps = match.groups()
        roles[role_name] = {
            "model_id": model_id.strip(),
            "pass_count": int(pass_count),
            "tokens_per_second": float(tps),
            "family": family.strip(),
        }

    # Validate constraints
    if roles["judge"]["family"] == roles["primary"]["family"]:
        raise ValueError("Judge family must differ from primary family")

    bar = promotion_bar()
    if roles["primary"]["pass_count"] < bar.primary_min_passing_cases:
        raise ValueError(
            f"Primary pass count {roles['primary']['pass_count']} "
            f"is less than required {bar.primary_min_passing_cases}"
        )

    return {"status": status, "roles": roles}
