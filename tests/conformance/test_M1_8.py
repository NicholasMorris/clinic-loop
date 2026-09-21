"""Conformance tests for M1-8: Cohort and corpus generation."""

import pytest

# This file marks M1-8 as a conformance issue
# The individual tests are in tests/world/cohorts/ and tests/world/corpus/
# This file serves as the conformance registration point

pytestmark = [
    pytest.mark.conformance_M1_8,
    pytest.mark.checklist_id("C0"),
    pytest.mark.checklist_id("R6"),
]
