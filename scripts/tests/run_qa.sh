#!/bin/bash
# Visual QA runner for SAT math generators.
# Installs dependencies on first run, then launches visual_qa.py.
#
# Usage:
#   ./scripts/tests/run_qa.sh                                  # all skills
#   ./scripts/tests/run_qa.sh --skill=linear_eq_one_var        # one skill
#   ./scripts/tests/run_qa.sh --skill=linear_eq_one_var,linear_functions
#   ./scripts/tests/run_qa.sh --skill=linear_eq_one_var --seed=123

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SAT_ENGINE_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
VENV="$SCRIPT_DIR/.venv"
VENV_PYTHON="$VENV/bin/python3"
VENV_PIP="$VENV/bin/pip"

echo "=== SAT Visual QA ==="
echo ""

# ── Python check ──────────────────────────────────────────────────────────────
if ! command -v python3 &>/dev/null; then
  echo "ERROR: python3 not found. Install Python 3.10+ and retry."
  exit 1
fi

# ── Create venv on first run ──────────────────────────────────────────────────
if [ ! -f "$VENV_PYTHON" ]; then
  echo "Creating virtual environment at scripts/tests/.venv ..."
  python3 -m venv "$VENV"
fi

# ── Install packages into venv if missing ────────────────────────────────────
if ! "$VENV_PYTHON" -c "import playwright" 2>/dev/null; then
  echo "Installing playwright into venv..."
  "$VENV_PIP" install --quiet playwright
fi

if ! "$VENV_PYTHON" -c "import anthropic" 2>/dev/null; then
  echo "Installing anthropic into venv..."
  "$VENV_PIP" install --quiet anthropic
fi

# ── Install Chromium browser if missing ───────────────────────────────────────
if ! "$VENV_PYTHON" -c "
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch()
    b.close()
" 2>/dev/null; then
  echo "Installing Chromium browser..."
  "$VENV/bin/playwright" install chromium
fi

# ── API key check ─────────────────────────────────────────────────────────────
if [ -z "$ANTHROPIC_API_KEY" ]; then
  echo "ERROR: ANTHROPIC_API_KEY is not set."
  echo "       Run: export ANTHROPIC_API_KEY=sk-ant-..."
  exit 1
fi

echo "Dependencies OK."
echo ""

# ── Run QA using venv Python ──────────────────────────────────────────────────
cd "$SAT_ENGINE_DIR"
"$VENV_PYTHON" scripts/tests/visual_qa.py "$@"
