#!/bin/bash
# Build and publish documentation to GitHub Pages

set -e

# Get the repository root
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# Build the MkDocs site in strict mode
echo "Building documentation with mkdocs build --strict..."
uv run --extra docs mkdocs build --strict

# Switch to gh-pages branch and commit the built site
echo "Committing built site to gh-pages branch..."

# Stash any uncommitted changes on the current branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
git stash push -u -m "docs_publish stash" || true

# Switch to gh-pages branch (or create if it doesn't exist)
if git rev-parse --verify gh-pages >/dev/null 2>&1; then
    git checkout gh-pages
    # Pull latest from origin if it exists
    git pull origin gh-pages 2>/dev/null || true
else
    # Create orphan gh-pages branch
    git checkout --orphan gh-pages
    git rm -rf . || true
fi

# Copy the built site from site/ directory to root
echo "Copying built site..."
# Remove all files except .git, site, and .gitignore
find . -maxdepth 1 -not -name '.git' -not -name 'site' -not -name '.gitignore' -delete
cp -r site/* .
rm -rf site

# Add all files
git add -A

# Commit with a timestamp
COMMIT_MESSAGE="docs: publish site on $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
if git diff-index --quiet --cached HEAD 2>/dev/null; then
    echo "No changes to commit"
else
    git commit -m "$COMMIT_MESSAGE"
fi

# Push to origin/gh-pages
echo "Pushing to origin/gh-pages..."
git push origin gh-pages

# Return to the original branch
echo "Returning to $CURRENT_BRANCH..."
git checkout "$CURRENT_BRANCH"

# Restore stashed changes if any
git stash pop || true

echo "Documentation published successfully!"
