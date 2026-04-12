#!/usr/bin/env bash
set -euo pipefail

# Usage: push-to-github.sh <cli-repo-path> [repo-name]
# Creates a new private GitHub repo and pushes the CLI

CLI_REPO="${1:?Usage: push-to-github.sh <cli-repo-path> [repo-name]}"
REPO_NAME="${2:-$(basename "$CLI_REPO")}"

cd "$CLI_REPO"

# Ensure we have a git repo with commits
if [ ! -d .git ]; then
  git init
  git add -A
  git commit -m "feat: initial CLI generation"
fi

# Check if remote already exists
if git remote get-url origin &>/dev/null; then
  echo '{"status":"error","message":"Remote origin already exists. Push manually or remove the remote first."}'
  exit 1
fi

# Create GitHub repo (private by default)
gh repo create "$REPO_NAME" --private --source=. --push

# Output result
REPO_URL=$(gh repo view --json url -q '.url')
echo "{\"status\":\"success\",\"repo_url\":\"$REPO_URL\",\"repo_name\":\"$REPO_NAME\"}"
