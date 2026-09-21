"""Test AC7: ADR parsing and validation."""

from pathlib import Path

from clinicloop.evals.toolcall.adr import parse_model_selection_adr
from clinicloop.evals.toolcall.thresholds import promotion_bar


def test_adr_roles_carry_numbers_families_and_clear_the_bar() -> None:
    """AC7: ADR parses and validates model selection roles.

    The ADR at docs/adr/llm-model-selection.md must:
    - Have status 'Accepted'
    - Name exactly three roles: primary, judge, fallback
    - Each role carries: pass count, tokens-per-second, family
    - Judge family differs from primary family
    - Primary pass count >= promotion_bar().primary_min_passing_cases
    """
    adr_path = (
        Path(__file__).parent.parent.parent.parent / "docs" / "adr" / "llm-model-selection.md"
    )

    # Parse the ADR
    adr = parse_model_selection_adr(str(adr_path))

    # Check status
    assert adr["status"] == "Accepted", f"Expected status 'Accepted', got {adr['status']}"

    # Check roles are exactly primary, judge, fallback
    assert set(adr["roles"].keys()) == {"primary", "judge", "fallback"}, (
        f"Expected roles {{primary, judge, fallback}}, got {set(adr['roles'].keys())}"
    )

    # Each role must have the required fields
    for role_name, role_data in adr["roles"].items():
        assert "model_id" in role_data, f"Role {role_name} missing model_id"
        assert "pass_count" in role_data, f"Role {role_name} missing pass_count"
        assert "tokens_per_second" in role_data, f"Role {role_name} missing tokens_per_second"
        assert "family" in role_data, f"Role {role_name} missing family"

        # Validate numeric fields
        assert isinstance(role_data["pass_count"], int), (
            f"Role {role_name} pass_count must be int, got {type(role_data['pass_count'])}"
        )
        assert isinstance(role_data["tokens_per_second"], (int, float)), (
            f"Role {role_name} tokens_per_second must be numeric"
        )

    # Judge family must differ from primary family
    primary_family = adr["roles"]["primary"]["family"]
    judge_family = adr["roles"]["judge"]["family"]
    assert primary_family != judge_family, (
        f"Judge family must differ from primary; both are {primary_family}"
    )

    # Primary pass count must meet or exceed the bar
    bar = promotion_bar()
    primary_pass_count = adr["roles"]["primary"]["pass_count"]
    assert primary_pass_count >= bar.primary_min_passing_cases, (
        f"Primary pass count {primary_pass_count} < required {bar.primary_min_passing_cases}"
    )


def test_adr_pass_counts_equal_counts_recomputed_from_records() -> None:
    """Every model's pass count in the ADR equals the count recomputed from its committed record."""
    import json
    from pathlib import Path

    root = Path(__file__).resolve().parents[3]
    adr = (root / "docs" / "adr" / "llm-model-selection.md").read_text()
    records = sorted((root / "evals" / "results" / "toolcall").glob("*.jsonl"))
    assert len(records) >= 3, "expected committed records for the measured models"
    for path in records:
        record = json.loads(path.read_text().splitlines()[0])
        passed = sum(
            1
            for case in record["per_case_results"]
            if case["emitted_tool_call"] and case["tool_name_matches"] and case["arguments_valid"]
        )
        assert f"**{record['model_id']}**: {passed}/30 passing" in adr, (
            f"ADR pass count for {record['model_id']} does not match the record ({passed}/30)"
        )
