#!/bin/bash
set -euo pipefail

# Only run in remote Claude Code on the web environment
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

# Ensure the workspace directory exists and is accessible
cd "${CLAUDE_PROJECT_DIR:-$(pwd)}"

# Verify git is available and the repo is healthy
git status --short > /dev/null 2>&1 || git init

echo "Workspace initialized successfully."
