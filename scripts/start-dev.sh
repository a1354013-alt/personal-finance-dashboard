#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKEND_DIR="$REPO_ROOT/backend"
FRONTEND_DIR="$REPO_ROOT/frontend"
VENV_DIR="$BACKEND_DIR/.venv"
VENV_PYTHON="$VENV_DIR/bin/python"

ensure_env_file() {
  local example_path="$1"
  local target_path="$2"

  if [ ! -f "$target_path" ] && [ -f "$example_path" ]; then
    cp "$example_path" "$target_path"
    echo "Created $(basename "$target_path") from $(basename "$example_path")."
  fi
}

port_in_use() {
  local port="$1"

  if command -v lsof >/dev/null 2>&1; then
    lsof -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1
    return $?
  fi

  if command -v ss >/dev/null 2>&1; then
    ss -ltn "( sport = :$port )" | tail -n +2 | grep -q .
    return $?
  fi

  if command -v netstat >/dev/null 2>&1; then
    netstat -an 2>/dev/null | grep -E "[\.\:]$port[[:space:]].*LISTEN" >/dev/null
    return $?
  fi

  return 1
}

command -v python3 >/dev/null 2>&1 || { echo "python3 is required."; exit 1; }
command -v node >/dev/null 2>&1 || { echo "node is required."; exit 1; }
command -v npm >/dev/null 2>&1 || { echo "npm is required."; exit 1; }

ensure_env_file "$BACKEND_DIR/.env.example" "$BACKEND_DIR/.env"
ensure_env_file "$FRONTEND_DIR/.env.example" "$FRONTEND_DIR/.env"

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

if port_in_use 8000; then
  echo "Port 8000 is already in use. Please close the existing backend server or change the port."
  exit 1
fi

if port_in_use 5173; then
  echo "Port 5173 is already in use. Please close the existing frontend server or change the port."
  exit 1
fi

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
