"""Conformance test registry: maps requirement IDs to test node IDs."""

import ast
import pkgutil
from pathlib import Path
from typing import Dict, List


def build_coverage_report() -> Dict[str, List[str]]:
    """Build a coverage report mapping requirement IDs to test node IDs.

    Discovers all test modules under tests/conformance and extracts their
    checklist_id markers to build a mapping from requirement identifier to
    test node IDs.

    Returns:
        A mapping of requirement identifier to a list of test node IDs that
        carry the checklist_id marker for that requirement.
    """
    report: Dict[str, List[str]] = {}

    conformance_dir = Path(__file__).parent

    # Discover all test modules under tests/conformance
    for importer, modname, ispkg in pkgutil.iter_modules([str(conformance_dir)]):
        if modname.startswith("test_") and modname not in ("test_registry",):
            module_path = conformance_dir / f"{modname}.py"

            # Parse the module to find checklist_id markers
            with open(module_path) as f:
                try:
                    tree = ast.parse(f.read())
                except SyntaxError:
                    continue

            # Find all functions/classes with checklist_id marker
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Check for checklist_id decorator
                    for decorator in node.decorator_list:
                        checklist_id = _extract_checklist_id(decorator)
                        if checklist_id:
                            test_node_id = f"tests/conformance/{modname}.py::{node.name}"
                            if checklist_id not in report:
                                report[checklist_id] = []
                            report[checklist_id].append(test_node_id)

    return report


def _extract_checklist_id(decorator: ast.expr) -> str | None:
    """Extract checklist_id from a pytest marker decorator.

    Args:
        decorator: An AST node representing a decorator.

    Returns:
        The checklist_id value if the decorator is a checklist_id marker,
        or None otherwise.
    """
    # Check for @pytest.mark.checklist_id("ID") pattern
    if isinstance(decorator, ast.Call):
        func = decorator.func
        if isinstance(func, ast.Attribute):
            if (isinstance(func.value, ast.Attribute) and
                func.value.attr == "mark" and
                func.attr == "checklist_id"):
                # Extract the argument
                if decorator.args:
                    arg = decorator.args[0]
                    if isinstance(arg, ast.Constant):
                        return str(arg.value)
    return None
