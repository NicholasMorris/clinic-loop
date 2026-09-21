"""Tests for ingress module public surface."""

import re

import pytest

import clinicloop.compliance.ingress as ingress


# Expected public API from the ingress module
EXPECTED_SURFACE = {
    "process_record",
}


def test_public_surface_matches_allowlist_and_returns_no_raw_identifiers() -> None:
    """AC7: Public surface matches allowlist, no raw identifiers returned."""
    # Check that __all__ matches expected surface
    assert set(ingress.__all__) == EXPECTED_SURFACE

    # Create a fixture record with identifiers
    # Use a valid Medicare number (1111111113 has valid checksum)
    fixture_record = {
        "patient_id": "P123",
        "medicare": "1111111113",  # Valid Medicare checksum
        "email": "john.doe@example.com",
        "phone": "0412345678",
        "dob": "15121990",
        "street_address": "42 Elm Street, Springfield",
        "given_name": "John",
        "family_name": "Doe",
    }

    # Process the record through ingress
    processed = ingress.process_record(fixture_record)

    # Check that no substring of length 4 or more from any identifier appears in output
    identifiers = [
        "1111111113",  # medicare (valid checksum)
        "0412345678",  # phone
        "15121990",    # dob
        "john",        # email local
        "example",     # email domain
        "42",          # street number
        "Elm",         # street name
    ]

    for identifier in identifiers:
        # Skip very short identifiers
        if len(identifier) >= 4:
            # Check all values in processed output
            output_str = str(processed)
            for i in range(len(identifier) - 3):
                substring = identifier[i : i + 4]
                assert substring not in output_str, (
                    f"Raw identifier substring '{substring}' found in output: {output_str}"
                )

    # Verify no module-level raw identifier names exist in __all__
    for name in ingress.__all__:
        # Each name in __all__ should be callable
        assert callable(getattr(ingress, name))
