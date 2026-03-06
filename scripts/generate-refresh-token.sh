#!/usr/bin/env bash
# Generate a Google Ads refresh token and save it to .env.
# Usage: ./scripts/generate-refresh-token.sh [--env-file /path/to/.env]
set -e

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

if ! command -v uv &>/dev/null; then
    echo "ERROR: uv is not installed."
    echo "Install it: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

cd "$REPO_ROOT"
uv run scripts/get_refresh_token.py "$@"
