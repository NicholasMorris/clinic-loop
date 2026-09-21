"""Test that cohort generation is deterministic per seed."""

import hashlib
import json

from clinicloop.world.cohorts import generate_cohorts


def test_cohort_set_is_seed_reproducible() -> None:
    """Test that cohort generation is deterministic and seed-dependent.

    generate_cohorts(seed=20260921) called twice produces JSON exports with
    equal SHA-256 digests, and seed=20260922 produces a different digest.
    """
    # Generate cohorts twice with the same seed
    cohorts1, ground_truth1 = generate_cohorts(seed=20260921)
    cohorts2, ground_truth2 = generate_cohorts(seed=20260921)

    # Generate cohorts with a different seed
    cohorts3, ground_truth3 = generate_cohorts(seed=20260922)

    # Convert to JSON for hashing
    def to_json_string(obj: object) -> str:
        """Convert object to canonical JSON string."""
        return json.dumps(obj, sort_keys=True, default=str)

    def compute_digest(obj: object) -> str:
        """Compute SHA-256 digest of JSON representation."""
        json_str = to_json_string(obj)
        return hashlib.sha256(json_str.encode()).hexdigest()

    digest1 = compute_digest((cohorts1, ground_truth1))
    digest2 = compute_digest((cohorts2, ground_truth2))
    digest3 = compute_digest((cohorts3, ground_truth3))

    assert digest1 == digest2, (
        f"Same seed (20260921) produced different digests: {digest1} != {digest2}"
    )
    assert digest1 != digest3, f"Different seeds produced same digest: {digest1} == {digest3}"
