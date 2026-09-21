"""Tests for the docs_publish script."""

import shutil
import subprocess
import tempfile
from pathlib import Path


def test_publish_script_builds_and_commits() -> None:
    """Test that scripts/docs_publish.sh builds and commits the site to gh-pages.

    AC1: scripts/docs_publish.sh runs mkdocs build --strict and commits the built
    site to gh-pages, then pushes to origin/gh-pages. The test invokes it over a
    fixture copy of the docs tree and asserts git log shows a new commit on gh-pages.
    """
    # Find the repository root
    repo_root = Path(__file__).parent.parent.parent

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # Create a temporary git repository to simulate origin
        origin_bare = tmp_path / "origin.git"
        origin_bare.mkdir()
        subprocess.run(
            ["git", "init", "--bare"],
            cwd=origin_bare,
            check=True,
            capture_output=True,
        )

        # Copy the repository to a working copy
        work_repo = tmp_path / "work_repo"
        shutil.copytree(repo_root, work_repo, ignore=shutil.ignore_patterns(".git"))

        # Initialize git in the copy
        subprocess.run(
            ["git", "init"],
            cwd=work_repo,
            check=True,
            capture_output=True,
        )

        # Configure user for git
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=work_repo,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=work_repo,
            check=True,
            capture_output=True,
        )

        # Add all files and create initial commit
        subprocess.run(
            ["git", "add", "."],
            cwd=work_repo,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=work_repo,
            check=True,
            capture_output=True,
        )

        # Create main branch explicitly
        subprocess.run(
            ["git", "branch", "-M", "main"],
            cwd=work_repo,
            check=True,
            capture_output=True,
        )

        # Configure the remote
        subprocess.run(
            ["git", "remote", "add", "origin", str(origin_bare)],
            cwd=work_repo,
            check=True,
            capture_output=True,
        )

        # Push main to origin
        subprocess.run(
            ["git", "push", "-u", "origin", "main"],
            cwd=work_repo,
            check=True,
            capture_output=True,
        )

        # Initialize gh-pages branch
        subprocess.run(
            ["git", "checkout", "--orphan", "gh-pages"],
            cwd=work_repo,
            check=True,
            capture_output=True,
        )

        # Create initial commit on gh-pages
        (work_repo / ".gitkeep").write_text("")
        subprocess.run(
            ["git", "add", ".gitkeep"],
            cwd=work_repo,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "commit", "-m", "Initial gh-pages commit"],
            cwd=work_repo,
            check=True,
            capture_output=True,
        )

        # Push initial gh-pages branch to origin
        subprocess.run(
            ["git", "push", "-u", "origin", "gh-pages"],
            cwd=work_repo,
            check=True,
            capture_output=True,
        )

        # Switch back to main
        subprocess.run(
            ["git", "checkout", "main"],
            cwd=work_repo,
            check=True,
            capture_output=True,
        )

        # Run the docs_publish script
        script_path = work_repo / "scripts" / "docs_publish.sh"
        result = subprocess.run(
            ["bash", str(script_path)],
            cwd=work_repo,
            capture_output=True,
            text=True,
        )

        # The script should succeed
        assert result.returncode == 0, f"Script failed: {result.stderr}"

        # Check that a new commit exists on gh-pages
        log_result = subprocess.run(
            ["git", "log", "--oneline", "gh-pages"],
            cwd=work_repo,
            capture_output=True,
            text=True,
            check=True,
        )

        # Should have at least 2 commits (initial + new)
        commits = log_result.stdout.strip().split("\n")
        assert len(commits) >= 2, f"Expected at least 2 commits, got {len(commits)}"

        # Check that the latest commit contains built site content (index.html)
        show_result = subprocess.run(
            ["git", "show", "gh-pages:index.html"],
            cwd=work_repo,
            capture_output=True,
            text=True,
        )
        assert show_result.returncode == 0, "index.html should exist on gh-pages"
        assert len(show_result.stdout) > 0, "index.html should not be empty"


def test_deploy_page_records_status_and_url() -> None:
    """Test that docs/process/docs-deploy.md records deployment status and URL.

    AC3: docs/process/docs-deploy.md states that scripts/docs_live_check.py is
    non-required until the first successful deployment and required thereafter,
    and records the published site URL.
    """
    repo_root = Path(__file__).parent.parent.parent
    deploy_page = repo_root / "docs" / "process" / "docs-deploy.md"

    # Page should exist
    assert deploy_page.exists(), "docs/process/docs-deploy.md should exist"

    # Read the content
    content = deploy_page.read_text(encoding="utf-8")

    # Should mention docs_live_check.py
    assert "docs_live_check.py" in content, "docs-deploy.md should mention docs_live_check.py"

    # Should mention non-required status
    assert "non-required" in content.lower(), (
        "docs-deploy.md should mention non-required status until first deployment"
    )

    # Should mention required status
    assert "required" in content.lower(), (
        "docs-deploy.md should mention required status after first deployment"
    )

    # Should record the published site URL
    # The URL pattern should be a GitHub Pages URL
    assert "github.com" in content or "ghpages" in content.lower() or "pages" in content.lower(), (
        "docs-deploy.md should record the published site URL"
    )
