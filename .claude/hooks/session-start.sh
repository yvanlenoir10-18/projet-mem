#!/bin/bash
set -euo pipefail

# Move to project directory
cd "${CLAUDE_PROJECT_DIR:-$(pwd)}"

# Ensure git repo is healthy
git status --short > /dev/null 2>&1 || git init

# Configure git safe directory (prevents "dubious ownership" errors in containers)
git config --global --add safe.directory "${CLAUDE_PROJECT_DIR:-$(pwd)}" 2>/dev/null || true

# Ensure .claude directories exist and are writable
mkdir -p .claude/hooks
mkdir -p .claude/agents/engineering

# Warm up file system access
ls -la > /dev/null 2>&1

echo "Workspace ready."
