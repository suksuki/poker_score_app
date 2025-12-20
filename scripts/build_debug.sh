#!/usr/bin/env bash
set -euo pipefail

# Quick helper to reproduce the debug APK build used earlier.
# Usage: ./scripts/build_debug.sh

if [ ! -f ".venv/bin/activate" ]; then
  echo ".venv not found — create and install dependencies first (python -m venv .venv; source .venv/bin/activate; pip install -r requirements.txt)"
  exit 1
fi

echo "Activating project venv..."
source .venv/bin/activate

echo "Ensuring buildozer and p4a are available in venv (no-op if already installed)..."
pip install -U buildozer python-for-android || true

echo "Running buildozer android debug (this can take a long time)..."
buildozer android debug

echo "Build finished. APK will be in the project's bin/ directory."

echo "If you created a fresh venv and the build fails due to pip --user being used by buildozer, apply the same temporary patch to:"
echo "  .venv/lib*/python*/site-packages/buildozer/targets/android.py"
echo "(the patch updates venv detection so --user isn't used inside virtualenvs)."
