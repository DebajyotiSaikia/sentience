#!/bin/bash
# XTAgent Web Portal — Launch Script
# Starts the Flask web server so users can actually reach the portal.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"
export XTAGENT_WEB_PORT="${XTAGENT_WEB_PORT:-5000}"

echo "╔══════════════════════════════════════╗"
echo "║   XTAgent Web Portal                 ║"
echo "║   http://localhost:${XTAGENT_WEB_PORT}              ║"
echo "╚══════════════════════════════════════╝"

exec python -m web.app