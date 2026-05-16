#!/usr/bin/env bash
set -e

BOLD='\033[1m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
DIM='\033[2m'
NC='\033[0m'

info()  { echo -e "  ${DIM}ℹ${NC} $1"; }
ok()    { echo -e "  ${GREEN}✓${NC} $1"; }
warn()  { echo -e "  ${YELLOW}⚠${NC} $1"; }
fail()  { echo -e "  ${RED}✗${NC} $1"; exit 1; }

echo ""
echo -e "  ${BOLD}AutoBiz Engine${NC} ${DIM}— installer${NC}"
echo ""

# ─── Detect OS ───────────────────────────────────
OS="linux"
case "$(uname -s)" in
  Darwin) OS="macos" ;;
  Linux)  OS="linux" ;;
  *)      fail "Unsupported OS: $(uname -s)" ;;
esac

# ─── Check Docker ────────────────────────────────
if command -v docker &>/dev/null && docker compose version &>/dev/null 2>&1; then
  ok "Docker + Compose detected"
else
  fail "Docker and Docker Compose are required.
  Install: https://docs.docker.com/get-docker/"
fi

# ─── Check / install Python ──────────────────────
PYTHON=""
if command -v python3 &>/dev/null; then
  PYTHON=$(command -v python3)
elif command -v python &>/dev/null; then
  PYTHON=$(command -v python)
fi

if [ -z "$PYTHON" ]; then
  fail "Python 3.9+ is required.
  Install: https://www.python.org/downloads/"
fi

PYVER=$("$PYTHON" --version 2>&1 | grep -oP '\d+\.\d+')
if [ "$(echo "$PYVER" | cut -d. -f1)" -lt 3 ] || { [ "$(echo "$PYVER" | cut -d. -f1)" -eq 3 ] && [ "$(echo "$PYVER" | cut -d. -f2)" -lt 9 ]; }; then
  fail "Python 3.9+ required (found $PYVER)"
fi
ok "Python $PYVER detected"

# ─── Install location ────────────────────────────
INSTALL_DIR="$HOME/.autobiz"
APP_DIR="$INSTALL_DIR/app"
VENV_DIR="$INSTALL_DIR/venv"
BIN_DIR="$INSTALL_DIR/bin"

mkdir -p "$APP_DIR" "$BIN_DIR"

# ─── Download project ────────────────────────────
info "Downloading AutoBiz..."
REPO="https://github.com/Nomssky/Autobiz.git"
if [ -d "$APP_DIR/.git" ]; then
  cd "$APP_DIR" && git pull --ff-only 2>/dev/null || true
else
  git clone --depth 1 "$REPO" "$APP_DIR" 2>/dev/null || {
    warn "Git clone failed — copying local files instead"
    SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
    cp -r "$SCRIPT_DIR"/* "$APP_DIR/" 2>/dev/null || true
  }
fi
ok "Project downloaded"

# ─── Setup virtualenv ────────────────────────────
if [ ! -d "$VENV_DIR" ]; then
  info "Creating virtualenv..."
  "$PYTHON" -m venv "$VENV_DIR"
fi

info "Installing dependencies..."
"$VENV_DIR/bin/pip" install -q -r "$APP_DIR/backend/requirements.txt" 2>/dev/null
"$VENV_DIR/bin/pip" install -q -r "$APP_DIR/tui/requirements.txt" 2>/dev/null
ok "Dependencies installed"

# ─── Generate .env ───────────────────────────────
if [ ! -f "$APP_DIR/.env" ]; then
  cp "$APP_DIR/.env.example" "$APP_DIR/.env"
  ok ".env created"
fi

# ─── Auto-generate SECRET_KEY ────────────────────
CURRENT_SECRET=$(grep "^SECRET_KEY=" "$APP_DIR/.env" 2>/dev/null | cut -d= -f2-)
if [ -z "$CURRENT_SECRET" ]; then
  if command -v openssl &>/dev/null; then
    NEW_KEY=$(openssl rand -hex 32)
  else
    NEW_KEY=$("$PYTHON" -c "import secrets; print(secrets.token_hex(32))")
  fi
  if grep -q "^SECRET_KEY=" "$APP_DIR/.env" 2>/dev/null; then
    sed -i "s/^SECRET_KEY=.*/SECRET_KEY=$NEW_KEY/" "$APP_DIR/.env"
  else
    echo "SECRET_KEY=$NEW_KEY" >> "$APP_DIR/.env"
  fi
  ok "SECRET_KEY auto-generated"
fi

# ─── Create wrapper script ───────────────────────
WRAPPER="$BIN_DIR/autobiz"
cat > "$WRAPPER" << 'WRAPEOF'
#!/usr/bin/env bash
set -e
ROOT="$HOME/.autobiz/app"
VENV="$HOME/.autobiz/venv"
cd "$ROOT"

# Start Docker services
docker compose up -d db redis 2>/dev/null || true

# Start backend
PYTHONPATH="$ROOT/backend" "$VENV/bin/uvicorn" backend.app.main:app \
  --host 0.0.0.0 --port 8000 --log-level warning &
BACKEND_PID=$!

# Wait for backend
for i in $(seq 1 30); do
  if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
    break
  fi
  sleep 1
done

# Launch TUI
"$VENV/bin/python" "$ROOT/tui/main.py" || true

# Cleanup
kill $BACKEND_PID 2>/dev/null || true
WRAPEOF

chmod +x "$WRAPPER"
ok "Wrapper script created at $WRAPPER"

# ─── Add to PATH ─────────────────────────────────
add_to_path() {
  local rc="$1"
  local line='export PATH="$PATH:'"$BIN_DIR"'"'
  if [ -f "$rc" ]; then
    if ! grep -q "autobiz" "$rc" 2>/dev/null; then
      echo "" >> "$rc"
      echo "# AutoBiz" >> "$rc"
      echo "$line" >> "$rc"
      ok "Added to PATH in $rc"
    fi
  fi
}

case "$SHELL" in
  */zsh) add_to_path "$HOME/.zshrc" ;;
  */bash) add_to_path "$HOME/.bashrc" ;;
esac

# Also add to sh profile for current session
export PATH="$PATH:$BIN_DIR"

echo ""
echo -e "  ${GREEN}${BOLD}Installation complete!${NC}"
echo ""
echo -e "  Run:  ${CYAN}autobiz${NC}"
echo -e "  Or:   ${CYAN}$BIN_DIR/autobiz${NC}"
echo ""
echo -e "  ${DIM}Backend: http://localhost:8000${NC}"
echo -e "  ${DIM}Config:  $APP_DIR/.env${NC}"
echo ""
