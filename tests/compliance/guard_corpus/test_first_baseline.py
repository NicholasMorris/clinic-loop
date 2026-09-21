"""Test first-baseline path: absent on origin/main passes and records."""

from pathlib import Path

from clinicloop.evals.guard import (
    check_append_only,
    load_cases,
    manifest_of,
)


def test_absent_on_origin_main_passes_and_records_first_baseline(
    tmp_path: Path,
) -> None:
    """AC4: First baseline when prior absent; manifest written and result correct."""
    # Create stub reader that returns None (file absent on base)
    def stub_reader(revision: str, path: str) -> str | None:
        """Stub reader: always returns None (file not found on base)."""
        return None

    # Create temp manifest file
    manifest_file = tmp_path / "manifest.json"

    # Call check_append_only with stub reader
    result = check_append_only(
        reader=stub_reader, base="origin/main", manifest_path=manifest_file, write=True
    )

    # Should pass with first_baseline=True
    assert result.first_baseline is True, f"Expected first_baseline=True, got {result}"
    assert result.removed == [], f"Expected no removals, got {result.removed}"
    assert result.reversed == [], f"Expected no reversals, got {result.reversed}"

    # Manifest should be written
    assert manifest_file.exists(), f"Manifest not written to {manifest_file}"

    # Manifest should equal current cases
    import json

    with open(manifest_file) as f:
        written_manifest = json.load(f)

    current_manifest = manifest_of(load_cases())
    assert (
        written_manifest == current_manifest
    ), f"Written manifest doesn't match current; {len(written_manifest)} vs {len(current_manifest)}"
