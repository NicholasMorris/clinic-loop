"""AC6: Stream isolation - message stream does not perturb patient IDs."""

import pytest

from clinicloop.world.generator import generate_world


@pytest.mark.checklist_id("AC6")
def test_message_stream_does_not_perturb_patient_ids() -> None:
    """Test that consuming from message stream does not affect patient generation.

    Verifies that each entity family has its own independent numpy.random.Generator
    stream, so consuming values from one stream does not affect generation from others.
    """
    # This test is a stub that will be implemented after the stream isolation
    # mechanism is built. For now, it serves as a placeholder to verify the
    # acceptance criterion framework is in place.
    pytest.skip("Stream isolation mechanism not yet implemented")
