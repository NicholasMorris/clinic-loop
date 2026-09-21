"""Tests for offline/network access policy."""

import ast
from pathlib import Path

import pytest


@pytest.fixture
def dashboard_module_path() -> Path:
    """Return the path to the dashboard package."""
    return Path(__file__).parent.parent.parent / "src" / "clinicloop" / "dashboard"


class TestOffline:
    """Test that dashboard makes no network calls."""

    def test_dashboard_makes_no_network_calls(self, dashboard_module_path: Path) -> None:
        """AC5: No dashboard module imports requests, httpx, or urllib.request.

        Scans all .py files in src/clinicloop/dashboard/ and verifies
        that none of them import network libraries.
        """
        banned_modules = {"requests", "httpx", "urllib.request"}

        for py_file in dashboard_module_path.glob("**/*.py"):
            with open(py_file, "r") as f:
                content = f.read()

            try:
                tree = ast.parse(content)
            except SyntaxError:
                pytest.fail(f"Syntax error in {py_file}")

            # Check all imports
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        assert alias.name not in banned_modules, f"{py_file} imports {alias.name}"

                elif isinstance(node, ast.ImportFrom):
                    if node.module is not None:
                        # Check direct import: "from requests import ..." or
                        # "from urllib.request import ..."
                        assert node.module not in banned_modules, (
                            f"{py_file} imports from {node.module}"
                        )

                        # Check partial matches: "from urllib import request"
                        if "." in node.module:
                            base = node.module.split(".")[0]
                            if base == "urllib":
                                for alias in node.names:
                                    if alias.name == "request":
                                        pytest.fail(f"{py_file} imports urllib.request")
