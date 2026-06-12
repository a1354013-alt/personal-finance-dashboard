#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKEND_DIR="$REPO_ROOT/backend"
FRONTEND_DIR="$REPO_ROOT/frontend"
VENV_DIR="$BACKEND_DIR/.venv"
VENV_PYTHON="$VENV_DIR/bin/python"

command -v python3 >/dev/null 2>&1 || { echo "python3 is required."; exit 1; }
command -v node >/dev/null 2>&1 || { echo "node is required."; exit 1; }
command -v npm >/dev/null 2>&1 || { echo "npm is required."; exit 1; }

if [ ! -x "$VENV_PYTHON" ]; then
  echo "Creating backend virtual environment..."
  python3 -m venv "$VENV_DIR"
fi

echo "Installing backend requirements..."
"$VENV_PYTHON" -m pip install -r "$BACKEND_DIR/requirements.txt"

echo "Applying backend migrations..."
(
  cd "$BACKEND_DIR"
  "$VENV_PYTHON" -m alembic upgrade head
)

echo "Installing frontend dependencies..."
(
  cd "$FRONTEND_DIR"
  if [ -f package-lock.json ]; then
    npm ci
  else
    npm install
  fi
)

echo "Starting backend and frontend dev servers..."
(
  cd "$BACKEND_DIR"
  "$VENV_PYTHON" -m uvicorn main:app --reload
) &
BACKEND_PID=$!

(
  cd "$FRONTEND_DIR"
  npm run dev
) &
FRONTEND_PID=$!

echo "Backend:  http://localhost:8000"
echo "Swagger:  http://localhost:8000/docs"
echo "Frontend: http://localhost:5173"
echo "Press Ctrl+C to stop both dev servers."

trap 'kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true' INT TERM EXIT
wait
