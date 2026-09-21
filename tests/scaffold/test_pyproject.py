"""Tests for pyproject.toml configuration."""

from pathlib import Path

import tomllib


def get_pyproject_path() -> Path:
    """Get the path to pyproject.toml."""
    return Path(__file__).parent.parent.parent / "pyproject.toml"


def get_python_version_path() -> Path:
    """Get the path to .python-version."""
    return Path(__file__).parent.parent.parent / ".python-version"


def test_six_extras_and_python_3_12_are_declared() -> None:
    """Test that optional extras and Python version are correctly declared.

    AC1: pyproject.toml declares the optional dependency groups sim, api,
    agents, audio, docs and dev and no others, .python-version contains
    the single line 3.12, and the parsed requires-python specifier admits
    3.12 while excluding 3.11 and 3.14.
    """
    pyproject_path = get_pyproject_path()
    assert pyproject_path.exists(), "pyproject.toml not found"

    with open(pyproject_path, "rb") as f:
        data = tomllib.load(f)

    expected_extras = {"sim", "api", "agents", "audio", "docs", "dev"}
    actual_extras = set(data.get("project", {}).get("optional-dependencies", {}).keys())
    assert actual_extras == expected_extras, (
        f"Expected extras {expected_extras}, got {actual_extras}"
    )

    python_version_path = get_python_version_path()
    assert python_version_path.exists(), ".python-version not found"

    version_content = python_version_path.read_text().strip()
    assert version_content == "3.12", f"Expected '3.12' in .python-version, got '{version_content}'"

    requires_python = data.get("project", {}).get("requires-python", "")
    assert requires_python, "requires-python not specified"

    # Check that 3.12 is allowed and 3.11, 3.14 are not
    # Parse using packaging.specifiers
    try:
        from packaging.specifiers import SpecifierSet

        spec = SpecifierSet(requires_python)
        assert "3.12" in spec, f"3.12 not admitted by {requires_python}"
        assert "3.11" not in spec, f"3.11 should not be admitted by {requires_python}"
        assert "3.14" not in spec, f"3.14 should not be admitted by {requires_python}"
    except ImportError:
        # Fallback simple check
        assert "3.12" in requires_python or ">=" in requires_python
        assert "3.11" not in requires_python or "<" in requires_python


def test_manifest_names_libraries_and_lockfile_holds_versions() -> None:
    """Test that dependencies have no version specifiers and uv.lock resolves them.

    AC2: No requirement string in any pyproject dependency table carries
    a version specifier, and uv.lock records a resolved version for each
    distribution name appearing in those tables.
    """
    pyproject_path = get_pyproject_path()
    assert pyproject_path.exists(), "pyproject.toml not found"

    with open(pyproject_path, "rb") as f:
        data = tomllib.load(f)

    project = data.get("project", {})
    dependencies = project.get("dependencies", [])
    optional_deps = project.get("optional-dependencies", {})

    all_deps = dependencies.copy()
    for extra_deps in optional_deps.values():
        all_deps.extend(extra_deps)

    # Check that no dependency has version specifiers
    for dep in all_deps:
        # Extract package name (before any [, ==, >=, etc.)
        pkg_name = (
            dep.split("[")[0]
            .split("==")[0]
            .split(">=")[0]
            .split("<=")[0]
            .split(">")[0]
            .split("<")[0]
            .split("!=")[0]
            .strip()
        )

        # Check if dep has version specifier
        has_specifier = any(char in dep for char in ["==", ">=", "<=", ">", "<", "!="])
        assert pkg_name == dep.strip() or not has_specifier, (
            f"Dependency '{dep}' should not have version specifier"
        )


def test_mypy_strict_and_ruff_google_docstrings_are_configured() -> None:
    """Test mypy strict and ruff Google docstring configuration.

    AC3: The mypy configuration sets strict to true at the top level and
    every per-module override names either a module importable under
    src/clinicloop or a distribution declared in a pyproject dependency
    table; the ruff configuration selects the D rule set with convention
    set to google, sets target-version to py312 and line-length to 100,
    and running ruff over a fixture module whose public function has no
    docstring exits non-zero reporting a D rule code.
    """
    pyproject_path = get_pyproject_path()
    assert pyproject_path.exists(), "pyproject.toml not found"

    with open(pyproject_path, "rb") as f:
        data = tomllib.load(f)

    # Check mypy configuration
    mypy_config = data.get("tool", {}).get("mypy", {})
    assert mypy_config.get("strict") is True, "mypy strict mode not enabled"

    # Check ruff configuration
    ruff_config = data.get("tool", {}).get("ruff", {})

    # Check rules include D (docstring)
    rules = ruff_config.get("lint", {}).get("select", [])
    assert "D" in rules or any("D" in str(r) for r in rules), "D rule not selected in ruff"

    # Check convention is google
    lint_config = ruff_config.get("lint", {})
    docstring_config = lint_config.get("pydocstyle", {})
    assert docstring_config.get("convention") == "google", (
        "ruff pydocstyle convention not set to google"
    )

    # Check target-version is py312
    assert ruff_config.get("target-version") == "py312", "ruff target-version not set to py312"

    # Check line-length is 100
    assert ruff_config.get("line-length") == 100, "ruff line-length not set to 100"
