"""AC1: World snapshot versioning and seed reproducibility."""

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from clinicloop.world.generator import generate_world, read_world_snapshot, write_world_snapshot


def _compute_sha256(path: Path) -> str:
    """Compute SHA-256 digest of a file."""
    sha256 = hashlib.sha256()
    with open(path, "rb") as f:
        sha256.update(f.read())
    return sha256.hexdigest()


@pytest.mark.checklist_id("AC1")
def test_snapshot_is_versioned_and_seed_reproducible_across_processes(tmp_path: Path) -> None:
    """Test that snapshots are versioned and reproducible across processes.

    Verifies that:
    1. Calling generate_world twice with same arguments yields identical JSON files
    2. Each file contains schema_version == "1", seed, population_size, span_days
    3. Different seed yields different digest
    4. read_world_snapshot + re-export yields same digest
    5. Subprocess with different PYTHONHASHSEED produces identical digest
    """
    seed = 20260921
    population_size = 500
    span_days = 30

    # Test 1 & 2: Generate twice with same arguments
    world1 = generate_world(seed=seed, population_size=population_size, span_days=span_days)
    path1 = tmp_path / "snapshot1.json"
    write_world_snapshot(world1, path1)

    world2 = generate_world(seed=seed, population_size=population_size, span_days=span_days)
    path2 = tmp_path / "snapshot2.json"
    write_world_snapshot(world2, path2)

    # Check digests match
    digest1 = _compute_sha256(path1)
    digest2 = _compute_sha256(path2)
    assert digest1 == digest2, "Identical arguments should produce identical snapshots"

    # Check schema_version and metadata in first file
    with open(path1) as f:
        data1 = json.load(f)
    assert data1["schema_version"] == "1"
    assert data1["seed"] == seed
    assert data1["population_size"] == population_size
    assert data1["span_days"] == span_days

    # Test 3: Different seed yields different digest
    world3 = generate_world(seed=20260922, population_size=population_size, span_days=span_days)
    path3 = tmp_path / "snapshot3.json"
    write_world_snapshot(world3, path3)
    digest3 = _compute_sha256(path3)
    assert digest3 != digest1, "Different seed should produce different snapshot"

    # Test 4: read_world_snapshot + re-export yields same digest
    world_read = read_world_snapshot(path1)
    path1_rewritten = tmp_path / "snapshot1_rewritten.json"
    write_world_snapshot(world_read, path1_rewritten)
    digest1_rewritten = _compute_sha256(path1_rewritten)
    assert digest1_rewritten == digest1, "Re-exporting should yield identical digest"

    # Test 5: Subprocess with different PYTHONHASHSEED
    script = f"""
import sys
sys.path.insert(0, {str(Path(__file__).parent.parent.parent.parent / "src")!r})

from clinicloop.world.generator import generate_world, write_world_snapshot
from pathlib import Path

world = generate_world(seed={seed}, population_size={population_size}, span_days={span_days})
write_world_snapshot(world, Path({str(tmp_path / "subprocess_output.json")!r}))
"""
    for hashseed in ["1", "random"]:
        env = {"PYTHONHASHSEED": hashseed}
        subprocess.run(
            [sys.executable, "-c", script],
            env=env,
            check=True,
            capture_output=True,
        )
        subprocess_path = tmp_path / "subprocess_output.json"
        subprocess_digest = _compute_sha256(subprocess_path)
        assert subprocess_digest == digest1, (
            f"PYTHONHASHSEED={hashseed} should match in-process digest"
        )
