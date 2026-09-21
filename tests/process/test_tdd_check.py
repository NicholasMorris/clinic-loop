"""AC1: tdd_check verifies red commits have tests that fail for the right reasons."""

import subprocess
from pathlib import Path

import pytest


def _init_git_repo(repo_path: Path) -> None:
    """Initialize a git repository with an initial commit.

    Args:
        repo_path: Path to the repository to initialize.
    """
    subprocess.run(
        ["git", "init"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )
    # Create initial commit
    (repo_path / "README.md").write_text("# Test Repo\n")
    subprocess.run(
        ["git", "add", "README.md"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )


def _create_fixture_repo_assertion_error(tmp_path: Path) -> Path:
    """Create fixture: commit adds test that fails with AssertionError.

    Args:
        tmp_path: Temporary directory for the repository.

    Returns:
        Path to the repository.
    """
    repo_path = tmp_path / "repo_assertion"
    repo_path.mkdir()
    _init_git_repo(repo_path)

    # Create tests directory and failing test
    tests_dir = repo_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "__init__.py").write_text("")
    (tests_dir / "test_feature.py").write_text(
        "def test_something():\n    assert False, 'Expected to fail'\n"
    )

    # Create stubs in src
    src_dir = repo_path / "src"
    src_dir.mkdir()
    (src_dir / "__init__.py").write_text("")

    # Add files and commit
    subprocess.run(
        ["git", "add", "-A"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "Add failing test"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )

    return repo_path


def _create_fixture_repo_notimplemented(tmp_path: Path) -> Path:
    """Create fixture: commit adds test that fails with NotImplementedError from stub.

    Args:
        tmp_path: Temporary directory for the repository.

    Returns:
        Path to the repository.
    """
    repo_path = tmp_path / "repo_notimplemented"
    repo_path.mkdir()
    _init_git_repo(repo_path)

    # Create tests directory and failing test
    tests_dir = repo_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "__init__.py").write_text("")
    (tests_dir / "test_feature.py").write_text(
        "from src.feature import do_something\n\ndef test_something():\n    do_something()\n"
    )

    # Create stub in src that raises NotImplementedError
    src_dir = repo_path / "src"
    src_dir.mkdir()
    (src_dir / "__init__.py").write_text("")
    (src_dir / "feature.py").write_text(
        "def do_something():\n    raise NotImplementedError('stub')\n"
    )

    # Add files and commit
    subprocess.run(
        ["git", "add", "-A"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "Add failing test with stub"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )

    return repo_path


def _create_fixture_repo_collection_error(tmp_path: Path) -> Path:
    """Create fixture: commit adds test with collection error (e.g., syntax error).

    Args:
        tmp_path: Temporary directory for the repository.

    Returns:
        Path to the repository.
    """
    repo_path = tmp_path / "repo_collection_error"
    repo_path.mkdir()
    _init_git_repo(repo_path)

    # Create tests directory and test with syntax error
    tests_dir = repo_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "__init__.py").write_text("")
    (tests_dir / "test_feature.py").write_text("def test_something()\n    this is invalid syntax\n")

    # Create stubs in src
    src_dir = repo_path / "src"
    src_dir.mkdir()
    (src_dir / "__init__.py").write_text("")

    # Add files and commit
    subprocess.run(
        ["git", "add", "-A"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "Add test with syntax error"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )

    return repo_path


def _create_fixture_repo_import_error(tmp_path: Path) -> Path:
    """Create fixture: commit adds test with ImportError.

    Args:
        tmp_path: Temporary directory for the repository.

    Returns:
        Path to the repository.
    """
    repo_path = tmp_path / "repo_import_error"
    repo_path.mkdir()
    _init_git_repo(repo_path)

    # Create tests directory and test with import error
    tests_dir = repo_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "__init__.py").write_text("")
    (tests_dir / "test_feature.py").write_text(
        "from nonexistent_module import something\n\ndef test_something():\n    pass\n"
    )

    # Create stubs in src
    src_dir = repo_path / "src"
    src_dir.mkdir()
    (src_dir / "__init__.py").write_text("")

    # Add files and commit
    subprocess.run(
        ["git", "add", "-A"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "Add test with import error"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )

    return repo_path


def _create_fixture_repo_name_error(tmp_path: Path) -> Path:
    """Create fixture: commit adds test that fails with NameError.

    Args:
        tmp_path: Temporary directory for the repository.

    Returns:
        Path to the repository.
    """
    repo_path = tmp_path / "repo_name_error"
    repo_path.mkdir()
    _init_git_repo(repo_path)

    # Create tests directory and test with name error
    tests_dir = repo_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "__init__.py").write_text("")
    (tests_dir / "test_feature.py").write_text("def test_something():\n    undefined_variable\n")

    # Create stubs in src
    src_dir = repo_path / "src"
    src_dir.mkdir()
    (src_dir / "__init__.py").write_text("")

    # Add files and commit
    subprocess.run(
        ["git", "add", "-A"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "Add test with name error"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )

    return repo_path


def _create_fixture_repo_no_tests(tmp_path: Path) -> Path:
    """Create fixture: commit adds code but no test file.

    Args:
        tmp_path: Temporary directory for the repository.

    Returns:
        Path to the repository.
    """
    repo_path = tmp_path / "repo_no_tests"
    repo_path.mkdir()
    _init_git_repo(repo_path)

    # Create only src, no tests
    src_dir = repo_path / "src"
    src_dir.mkdir()
    (src_dir / "__init__.py").write_text("")
    (src_dir / "feature.py").write_text("def do_something():\n    pass\n")

    # Add files and commit
    subprocess.run(
        ["git", "add", "-A"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "Add implementation without tests"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )

    return repo_path


def _create_fixture_repo_attribute_error(tmp_path: Path) -> Path:
    """Create fixture: commit adds test that fails with AttributeError.

    Args:
        tmp_path: Temporary directory for the repository.

    Returns:
        Path to the repository.
    """
    repo_path = tmp_path / "repo_attribute_error"
    repo_path.mkdir()
    _init_git_repo(repo_path)

    # Create tests directory and test with attribute error
    tests_dir = repo_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "__init__.py").write_text("")
    (tests_dir / "test_feature.py").write_text(
        "class MyClass:\n    pass\n\n"
        "def test_something():\n    obj = MyClass()\n    obj.nonexistent_attr\n"
    )

    # Create stubs in src
    src_dir = repo_path / "src"
    src_dir.mkdir()
    (src_dir / "__init__.py").write_text("")

    # Add files and commit
    subprocess.run(
        ["git", "add", "-A"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "Add test with attribute error"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )

    return repo_path


@pytest.mark.checklist_id("P2")
def test_only_assertion_or_src_notimplemented_failures_are_accepted(
    tmp_path: Path,
) -> None:
    """AC1: tdd_check accepts AssertionError and src NotImplementedError, rejects others.

    Verifies against seven fixture git repositories:
    1. AssertionError - should accept (exit 0)
    2. NotImplementedError from src stub - should accept (exit 0)
    3. Pytest collection error (SyntaxError) - should reject (exit 1)
    4. ImportError - should reject (exit 1)
    5. NameError - should reject (exit 1)
    6. No tests added - should reject (exit 1)
    7. AttributeError - should reject (exit 1)
    """
    # Create all fixture repositories
    fixtures = [
        ("assertion_error", _create_fixture_repo_assertion_error(tmp_path), 0),
        ("notimplemented", _create_fixture_repo_notimplemented(tmp_path), 0),
        ("collection_error", _create_fixture_repo_collection_error(tmp_path), 1),
        ("import_error", _create_fixture_repo_import_error(tmp_path), 1),
        ("name_error", _create_fixture_repo_name_error(tmp_path), 1),
        ("no_tests", _create_fixture_repo_no_tests(tmp_path), 1),
        ("attribute_error", _create_fixture_repo_attribute_error(tmp_path), 1),
    ]

    # Find tdd_check script
    repo_root = Path(__file__).parent.parent.parent
    tdd_check_script = repo_root / "scripts" / "process" / "tdd_check.py"
    assert tdd_check_script.exists(), f"tdd_check not found at {tdd_check_script}"

    # Test each fixture
    for name, repo_path, expected_exit_code in fixtures:
        # Get the head commit SHA
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True,
        )
        commit_sha = result.stdout.strip()

        # Run tdd_check on the latest commit
        result = subprocess.run(
            ["python", str(tdd_check_script), str(repo_path), commit_sha],
            capture_output=True,
            text=True,
        )

        assert result.returncode == expected_exit_code, (
            f"Fixture {name}: expected exit {expected_exit_code}, "
            f"got {result.returncode}\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )
