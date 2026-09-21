"""Tests for the pyproject.toml manifest, its lockfile and the lint and type configuration."""

import re
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any

from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging.utils import canonicalize_name
from packaging.version import Version

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_PACKAGE = REPO_ROOT / "src" / "clinicloop"

EXPECTED_EXTRAS = {"sim", "api", "agents", "audio", "docs", "dev"}

PLANNED_LIBRARIES = {
    "langgraph",
    "langgraph-checkpoint-sqlite",
    "langchain-core",
    "langchain-openai",
    "pydantic",
    "numpy",
    "fastapi",
    "uvicorn",
    "httpx",
    "streamlit",
    "soundfile",
    "silero-vad",
    "speechbrain",
    "pytest",
    "pytest-socket",
    "ruff",
    "mypy",
    "towncrier",
    "mkdocs",
    "mkdocs-material",
    "mkdocs-awesome-nav",
}

SCRIPT_MODULES = {"clinicloop.setup.doctor", "clinicloop.setup.install"}


def load_pyproject() -> dict[str, Any]:
    """Parse the repository pyproject.toml.

    Returns:
        The parsed TOML document.
    """
    with open(REPO_ROOT / "pyproject.toml", "rb") as handle:
        return tomllib.load(handle)


def requirement_strings(data: dict[str, Any]) -> list[str]:
    """Collect every requirement string from every pyproject dependency table.

    Args:
        data: The parsed pyproject document.

    Returns:
        Requirement strings from project dependencies, every optional extra, any dependency
        group and the build-system requirements.
    """
    project = data.get("project", {})
    found: list[str] = list(project.get("dependencies", []))
    for extra_requirements in project.get("optional-dependencies", {}).values():
        found.extend(extra_requirements)
    for group in data.get("dependency-groups", {}).values():
        found.extend(item for item in group if isinstance(item, str))
    found.extend(data.get("build-system", {}).get("requires", []))
    return found


def declared_distributions(data: dict[str, Any]) -> set[str]:
    """Return the normalised distribution names from every dependency table.

    Args:
        data: The parsed pyproject document.

    Returns:
        Canonicalised distribution names.
    """
    return {canonicalize_name(Requirement(item).name) for item in requirement_strings(data)}


def run_git(*args: str) -> subprocess.CompletedProcess[str]:
    """Run git inside the repository and capture its output.

    Args:
        *args: Arguments passed to git.

    Returns:
        The completed process.
    """
    return subprocess.run(
        ["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=False
    )


def test_six_extras_and_python_3_12_are_declared() -> None:
    """AC1: six extras and no others, single-line .python-version, 3.12-only specifier."""
    data = load_pyproject()

    actual_extras = set(data["project"]["optional-dependencies"])
    assert actual_extras == EXPECTED_EXTRAS, f"expected {EXPECTED_EXTRAS}, got {actual_extras}"

    version_lines = (REPO_ROOT / ".python-version").read_text().splitlines()
    assert version_lines == ["3.12"], (
        f".python-version must be the single line 3.12: {version_lines}"
    )

    spec = SpecifierSet(data["project"]["requires-python"])
    assert "3.12" in spec, f"3.12 not admitted by {spec}"
    assert "3.11" not in spec, f"3.11 must be excluded by {spec}"
    assert "3.14" not in spec, f"3.14 must be excluded by {spec}"


def test_manifest_names_libraries_and_lockfile_holds_versions() -> None:
    """AC2: no version specifiers in the manifest, and uv.lock resolves every distribution."""
    data = load_pyproject()
    requirements = requirement_strings(data)
    assert requirements, "no requirement strings found in any dependency table"

    for text in requirements:
        parsed = Requirement(text)
        assert str(parsed.specifier) == "", f"{text!r} carries a version specifier"
        assert parsed.url is None, f"{text!r} pins a direct URL"

    lock_path = REPO_ROOT / "uv.lock"
    assert lock_path.is_file(), "uv.lock does not exist"
    assert run_git("ls-files", "--error-unmatch", "uv.lock").returncode == 0, "uv.lock not tracked"
    assert run_git("check-ignore", "-q", "uv.lock").returncode != 0, "uv.lock is gitignored"

    with open(lock_path, "rb") as handle:
        lock = tomllib.load(handle)
    resolved: dict[str, str] = {
        str(canonicalize_name(package["name"])): package.get("version", "")
        for package in lock.get("package", [])
    }

    declared = declared_distributions(data)
    assert declared >= PLANNED_LIBRARIES, (
        f"missing planned libraries: {PLANNED_LIBRARIES - declared}"
    )
    for name in sorted(declared):
        assert name in resolved, f"{name} is declared but absent from uv.lock"
        assert resolved[name], f"{name} has no resolved version in uv.lock"
        Version(resolved[name])


def test_manifest_spreads_planned_libraries_over_the_extras() -> None:
    """The planned libraries are declared, and every extra holds at least one library."""
    data = load_pyproject()
    extras = data["project"]["optional-dependencies"]
    for extra, items in extras.items():
        assert items, f"extra {extra} is empty"

    declared_in_extras = {
        canonicalize_name(Requirement(item).name) for items in extras.values() for item in items
    }
    assert declared_in_extras >= PLANNED_LIBRARIES, (
        f"planned libraries missing from the extras: {PLANNED_LIBRARIES - declared_in_extras}"
    )


def test_script_entry_points_and_typing_marker() -> None:
    """Entry points cover exactly the setup modules named in the issue and py.typed ships."""
    data = load_pyproject()
    scripts = data["project"]["scripts"]
    targets = {target.split(":")[0] for target in scripts.values()}
    assert targets == SCRIPT_MODULES, f"unexpected script targets: {targets}"

    assert "readme" not in data["project"], "readme key points at a file this issue does not own"

    marker = SRC_PACKAGE / "py.typed"
    assert marker.is_file(), "src/clinicloop/py.typed is missing"
    assert marker.stat().st_size == 0, "py.typed must be empty"
    assert run_git("ls-files", "--error-unmatch", "src/clinicloop/py.typed").returncode == 0
    package_data = data["tool"]["setuptools"]["package-data"]
    assert "py.typed" in package_data["clinicloop"], "py.typed is not declared as package data"


def override_modules(data: dict[str, Any]) -> list[str]:
    """List every module name named by a mypy per-module override.

    Args:
        data: The parsed pyproject document.

    Returns:
        The module patterns of every override, flattened.
    """
    modules: list[str] = []
    for override in data["tool"]["mypy"].get("overrides", []):
        named = override["module"]
        modules.extend([named] if isinstance(named, str) else named)
    return modules


def override_is_resolvable(module: str, distributions: set[str]) -> bool:
    """Decide whether an override module is a local module or a declared distribution.

    Args:
        module: A mypy override module pattern such as ``speechbrain.*``.
        distributions: Canonical distribution names from the dependency tables.

    Returns:
        True when the module lives under src/clinicloop or names a declared distribution.
    """
    parts = [part for part in module.split(".") if part != "*"]
    if parts[0] == "clinicloop":
        local = SRC_PACKAGE.joinpath(*parts[1:])
        return local.is_dir() or local.with_suffix(".py").is_file()
    return canonicalize_name(parts[0]) in distributions


def test_mypy_strict_and_ruff_google_docstrings_are_configured(tmp_path: Path) -> None:
    """AC3: mypy strict, resolvable overrides, and ruff Google docstrings that bite."""
    data = load_pyproject()

    mypy_config = data["tool"]["mypy"]
    assert mypy_config.get("strict") is True, "mypy strict must be true at the top level"
    distributions = declared_distributions(data)
    modules = override_modules(data)
    assert modules, "no per-module mypy overrides are declared"
    for module in modules:
        assert override_is_resolvable(module, distributions), (
            f"mypy override {module!r} is neither a clinicloop module nor a declared distribution"
        )
    assert not override_is_resolvable("nonexistent_distribution", distributions)

    ruff_config = data["tool"]["ruff"]
    assert "D" in ruff_config["lint"]["select"], "ruff must select the D rule set"
    assert ruff_config["lint"]["pydocstyle"]["convention"] == "google"
    assert ruff_config["target-version"] == "py312"
    assert ruff_config["line-length"] == 100

    undocumented = tmp_path / "undocumented_module.py"
    undocumented.write_text(
        '"""Module docstring."""\n\n\ndef public_function() -> int:\n    return 1\n'
    )
    documented = tmp_path / "documented_module.py"
    documented.write_text(
        '"""Module docstring."""\n\n\ndef public_function() -> int:\n'
        '    """Return one.\n\n    Returns:\n        The number one.\n    """\n    return 1\n'
    )
    config = str(REPO_ROOT / "pyproject.toml")
    base = [sys.executable, "-m", "ruff", "check", "--config", config, "--no-cache"]

    failing = subprocess.run(
        [*base, str(undocumented)], capture_output=True, text=True, check=False
    )
    assert failing.returncode != 0, "ruff accepted a public function with no docstring"
    assert re.search(r"\bD10\d\b", failing.stdout), f"no D rule code reported: {failing.stdout}"

    passing = subprocess.run([*base, str(documented)], capture_output=True, text=True, check=False)
    assert passing.returncode == 0, f"ruff rejected a documented module: {passing.stdout}"
