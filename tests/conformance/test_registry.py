"""Tests for the conformance registry."""

import pkgutil
from pathlib import Path

import pytest

from tests.conformance.registry import build_coverage_report


def test_every_conformance_module_declares_a_checklist_id() -> None:
    """AC3: Every conformance test module declares a checklist_id marker."""
    # Discover all test modules under tests/conformance
    conformance_dir = Path(__file__).parent
    test_modules = []

    for importer, modname, ispkg in pkgutil.iter_modules([str(conformance_dir)]):
        if modname.startswith("test_") and modname not in ("test_registry",):
            test_modules.append(modname)

    # Each module should have a checklist_id marker
    missing = []
    for modname in test_modules:
        # We'll check if the module has the marker by looking for pytest.mark.checklist_id
        # For now, we verify the marker exists in the test discovery
        module_path = conformance_dir / f"{modname}.py"
        content = module_path.read_text()
        if "checklist_id" not in content:
            missing.append(modname)

    assert not missing, f"Modules without checklist_id marker: {missing}"


@pytest.mark.checklist_id("ZZ9")
def test_coverage_report_maps_fixture_id_to_node_id() -> None:
    """AC4: build_coverage_report maps fixture ZZ9 to a test node ID."""
    report = build_coverage_report()
    assert "ZZ9" in report, f"Coverage report missing ZZ9. Got: {report}"
    assert isinstance(report["ZZ9"], list), (
        f"ZZ9 value should be a list, got {type(report['ZZ9'])}"
    )
    assert len(report["ZZ9"]) > 0, "ZZ9 should map to at least one test node ID"
    # The node ID should contain test_ZZ9
    assert any("test_ZZ9" in node_id for node_id in report["ZZ9"]), \
        f"Expected a test_ZZ9 node in {report['ZZ9']}"


def test_five_registered_identifiers_have_node_ids() -> None:
    """AC5: Coverage report maps {B1, D6, L1, L6, P4} to non-empty node-id lists."""
    report = build_coverage_report()
    required_ids = {"B1", "D6", "L1", "L6", "P4"}

    missing_ids = required_ids - set(report.keys())
    assert not missing_ids, f"Coverage report missing requirement IDs: {missing_ids}"

    for req_id in required_ids:
        node_ids = report[req_id]
        assert isinstance(node_ids, list), f"{req_id} value should be a list, got {type(node_ids)}"
        assert len(node_ids) > 0, f"{req_id} should map to at least one test node ID"
        # Each module should have a corresponding test file
        expected_module = f"test_{req_id}"
        assert any(expected_module in node_id for node_id in node_ids), \
            f"Expected a {expected_module} node in {node_ids}"
