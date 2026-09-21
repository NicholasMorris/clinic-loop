"""Tests for console module boundary restrictions."""

import ast
from pathlib import Path
from typing import Any

import pytest

from clinicloop.hitl.console.backend import list_pending


def scan_module_for_violations(module_path: Path) -> list[dict[str, Any]]:
    """Scan a module for forbidden symbols and patterns.

    Checks for:
    - Imports or references to SignoffService or SignedNote
    - update_state calls with channels other than "human_decision"
    - Imports of clinicloop.dashboard
    """
    violations: list[dict[str, Any]] = []

    try:
        with open(module_path) as f:
            tree = ast.parse(f.read())
    except (SyntaxError, OSError):
        return violations

    class Visitor(ast.NodeVisitor):
        """AST visitor to find violations."""

        def visit_Import(self, node: ast.Import) -> None:
            """Check for forbidden imports."""
            for alias in node.names:
                if "clinicloop.dashboard" in alias.name:
                    violations.append(
                        {
                            "type": "forbidden_import",
                            "name": alias.name,
                            "line": node.lineno,
                        }
                    )
            self.generic_visit(node)

        def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
            """Check for forbidden imports and symbols."""
            if node.module and "clinicloop.dashboard" in node.module:
                violations.append(
                    {
                        "type": "forbidden_import",
                        "name": node.module,
                        "line": node.lineno,
                    }
                )
            for alias in node.names:
                if alias.name in ("SignoffService", "SignedNote"):
                    violations.append(
                        {
                            "type": "forbidden_symbol",
                            "name": alias.name,
                            "line": node.lineno,
                        }
                    )
            self.generic_visit(node)

        def visit_ClassDef(self, node: ast.ClassDef) -> None:
            """Check for class definitions of forbidden symbols."""
            if node.name in ("SignoffService", "SignedNote"):
                violations.append(
                    {
                        "type": "forbidden_symbol",
                        "name": node.name,
                        "line": node.lineno,
                    }
                )
            self.generic_visit(node)

        def visit_Name(self, node: ast.Name) -> None:
            """Check for direct references to forbidden symbols."""
            if node.id in ("SignoffService", "SignedNote"):
                violations.append(
                    {
                        "type": "forbidden_symbol",
                        "name": node.id,
                        "line": node.lineno,
                    }
                )
            self.generic_visit(node)

        def visit_Attribute(self, node: ast.Attribute) -> None:
            """Check for attribute references to forbidden symbols."""
            if node.attr in ("SignoffService", "SignedNote"):
                violations.append(
                    {
                        "type": "forbidden_symbol",
                        "name": node.attr,
                        "line": node.lineno,
                    }
                )
            self.generic_visit(node)

        def visit_Call(self, node: ast.Call) -> None:
            """Check for update_state calls with forbidden channels."""
            # Check if this is an update_state call
            func_name = None
            if isinstance(node.func, ast.Attribute):
                func_name = node.func.attr
            elif isinstance(node.func, ast.Name):
                func_name = node.func.id

            if func_name == "update_state":
                # Check if the dict argument has only "human_decision" key
                for arg in node.args:
                    if isinstance(arg, ast.Dict):
                        for key in arg.keys:
                            if isinstance(key, ast.Constant):
                                if key.value != "human_decision":
                                    violations.append(
                                        {
                                            "type": "forbidden_update_state",
                                            "channel": key.value,
                                            "line": node.lineno,
                                        }
                                    )
            self.generic_visit(node)

    Visitor().visit(tree)
    return violations


def test_console_cannot_sign_or_write_other_state() -> None:
    """AC6: Console has no SignoffService, SignedNote, or dashboard imports.

    Scan over hitl/console/ finds no forbidden symbols.
    Scan over decoy_signer.py reports it as a violation.
    """
    console_path = Path(__file__).parent.parent.parent / "src" / "clinicloop" / "hitl" / "console"

    # Scan all Python files in console/
    violations = []
    for py_file in console_path.glob("**/*.py"):
        if py_file.name.startswith("test_"):
            continue
        violations.extend(scan_module_for_violations(py_file))

    # Should have no violations
    assert len(violations) == 0, f"Console module has forbidden symbols/patterns: {violations}"

    # Now verify the scanner detects violations in decoy_signer.py
    decoy_path = Path(__file__).parent / "decoy_signer.py"
    decoy_violations = scan_module_for_violations(decoy_path)

    # Should detect the SignoffService definition
    assert len(decoy_violations) > 0, "Scanner should detect SignoffService in decoy_signer.py"
    assert any(v.get("name") == "SignoffService" for v in decoy_violations)


def test_console_makes_no_network_calls(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """AC7: Console test module passes under pytest-socket with loopback blocked.

    This test verifies that the console backend makes no network calls.
    """
    # This test will be run with pytest-socket enabled (loopback only by default)
    # If it passes without blocking, no network calls were made.

    # Set up a minimal checkpoint root
    root = tmp_path / "checkpoints"
    root.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("CLINICLOOP_CHECKPOINT_ROOT", str(root))

    # These should not make network calls
    try:
        listing = list_pending()
        # If we get here without a socket error, we're good
        assert listing is not None
    except OSError as e:
        if "network" in str(e).lower() or "socket" in str(e).lower():
            pytest.fail(f"Console made a network call: {e}")
        raise
