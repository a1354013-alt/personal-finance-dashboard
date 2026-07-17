#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKEND_DIR="$REPO_ROOT/backend"
FRONTEND_DIR="$REPO_ROOT/frontend"
VENV_DIR="$BACKEND_DIR/.venv"
VENV_PYTHON="$VENV_DIR/bin/python"
REQ_STAMP="$VENV_DIR/.requirements.sha256"
PY_STAMP="$VENV_DIR/.python-version"
PKG_STAMP="$FRONTEND_DIR/node_modules/.package-lock.sha256"

ensure_env_file() {
  local example_path="$1"
  local target_path="$2"
  if [ ! -f "$target_path" ] && [ -f "$example_path" ]; then
    cp "$example_path" "$target_path"
    echo "Created $(basename "$target_path") from $(basename "$example_path")."
  fi
}

python_minor() {
  "$1" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")'
}

find_python() {
  for candidate in python3.12 python3.11 python3; do
    if command -v "$candidate" >/dev/null 2>&1; then
      version="$(python_minor "$candidate" || true)"
      if [ "$version" = "3.11" ] || [ "$version" = "3.12" ]; then
        command -v "$candidate"
        return 0
      fi
    fi
  done
  echo "Install Python 3.11 or 3.12 and ensure python3.11, python3.12, or python3 points to it." >&2
  return 1
}

check_node() {
  command -v node >/dev/null 2>&1 || { echo "node is required."; exit 1; }
  command -v npm >/dev/null 2>&1 || { echo "npm is required."; exit 1; }
  node -e 'const [M,m]=process.versions.node.split(".").map(Number); if (!((M===20&&m>=19)||(M===22&&m>=12))) { console.error(`Unsupported Node ${process.versions.node}. Use Node 20.19.x or Node 22.12.x+.`); process.exit(1); }'
}

hash_file() {
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$1" | awk '{print $1}'
  else
    shasum -a 256 "$1" | awk '{print $1}'
  fi
}

port_in_use() {
  local port="$1"
  if command -v lsof >/dev/null 2>&1; then lsof -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1; return $?; fi
  if command -v ss >/dev/null 2>&1; then ss -ltn "( sport = :$port )" | tail -n +2 | grep -q .; return $?; fi
  if command -v netstat >/dev/null 2>&1; then netstat -an 2>/dev/null | grep -E "[\.\:]$port[[:space:]].*LISTEN" >/dev/null; return $?; fi
  return 1
}

PYTHON_BIN="$(find_python)"
check_node
ensure_env_file "$BACKEND_DIR/.env.example" "$BACKEND_DIR/.env"
ensure_env_file "$FRONTEND_DIR/.env.example" "$FRONTEND_DIR/.env"

if [ -x "$VENV_PYTHON" ]; then
  VENV_VERSION="$(python_minor "$VENV_PYTHON" || true)"
  if [ "$VENV_VERSION" != "3.11" ] && [ "$VENV_VERSION" != "3.12" ]; then
    echo "Existing backend virtual environment uses unsupported Python $VENV_VERSION; recreating it."
    rm -rf "$VENV_DIR"
  else
    echo "Using existing backend virtual environment with Python $VENV_VERSION."
  fi
fi

if [ ! -x "$VENV_PYTHON" ]; then
  echo "Creating backend virtual environment with $("$PYTHON_BIN" --version)..."
  "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

VENV_VERSION="$(python_minor "$VENV_PYTHON")"
REQ_HASH="$(hash_file "$BACKEND_DIR/requirements.txt")"
REQ_STAMP_VALUE="$VENV_VERSION:$REQ_HASH"
INSTALLED_REQ_STAMP="$(cat "$REQ_STAMP" 2>/dev/null || true)"
INSTALLED_PY_STAMP="$(cat "$PY_STAMP" 2>/dev/null || true)"
if [ "$REQ_STAMP_VALUE" != "$INSTALLED_REQ_STAMP" ] || [ "$VENV_VERSION" != "$INSTALLED_PY_STAMP" ]; then
  echo "Installing backend requirements..."
  "$VENV_PYTHON" -m pip install -r "$BACKEND_DIR/requirements.txt"
  printf '%s\n' "$REQ_STAMP_VALUE" > "$REQ_STAMP"
  printf '%s\n' "$VENV_VERSION" > "$PY_STAMP"
else
  echo "Backend requirements already installed."
fi

echo "Applying backend migrations..."
(cd "$BACKEND_DIR" && "$VENV_PYTHON" -m alembic upgrade head)

PKG_HASH="$(hash_file "$FRONTEND_DIR/package.json")"
if [ -f "$FRONTEND_DIR/package-lock.json" ]; then
  PKG_HASH="$PKG_HASH:$(hash_file "$FRONTEND_DIR/package-lock.json")"
fi
INSTALLED_PKG_STAMP="$(cat "$PKG_STAMP" 2>/dev/null || true)"
if [ ! -d "$FRONTEND_DIR/node_modules" ] || [ "$PKG_HASH" != "$INSTALLED_PKG_STAMP" ]; then
  echo "Installing frontend dependencies..."
  (cd "$FRONTEND_DIR" && if [ -f package-lock.json ]; then npm ci; else npm install; fi)
  printf '%s\n' "$PKG_HASH" > "$PKG_STAMP"
else
  echo "Frontend dependencies already present."
fi

if port_in_use 8000; then echo "Port 8000 is already in use."; exit 1; fi
if port_in_use 5173; then echo "Port 5173 is already in use."; exit 1; fi

echo "Starting backend and frontend dev servers..."
(cd "$BACKEND_DIR" && "$VENV_PYTHON" -m uvicorn main:app --reload --host 127.0.0.1 --port 8000) &
BACKEND_PID=$!
(cd "$FRONTEND_DIR" && npm run dev -- --host 127.0.0.1 --port 5173) &
FRONTEND_PID=$!

trap 'kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true' INT TERM EXIT
echo "Backend:  http://127.0.0.1:8000"
echo "Swagger:  http://127.0.0.1:8000/docs"
echo "Frontend: http://127.0.0.1:5173"
wait
