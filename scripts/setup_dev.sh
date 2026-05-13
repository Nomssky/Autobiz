#!/bin/bash
# setup_dev.sh — AutoBiz Engine Developer Environment Setup
# Run: bash scripts/setup_dev.sh

set -e

echo "========================================"
echo "  AutoBiz Engine — Dev Environment Setup"
echo "========================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# ---- 1. Check requirements ----
log_info "Checking Python version..."
if ! command -v python3 &> /dev/null; then
    log_error "Python3 not found. Please install Python 3.11+"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
log_info "Python version: $PYTHON_VERSION"

if [[ "$PYTHON_VERSION" < "3.11" ]]; then
    log_warn "Python 3.11+ recommended. Some features may not work."
fi

# ---- 2. Create virtual environment ----
VENV_DIR=".venv"
if [ ! -d "$VENV_DIR" ]; then
    log_info "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
    log_info "Virtual environment created at $VENV_DIR"
else
    log_info "Virtual environment already exists at $VENV_DIR"
fi

# Activate virtual environment
log_info "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# ---- 3. Upgrade pip ----
log_info "Upgrading pip..."
pip install --upgrade pip setuptools wheel -q

# ---- 4. Install dependencies ----
log_info "Installing project dependencies..."

# Backend dependencies
if [ -f "backend/requirements.txt" ]; then
    pip install -r backend/requirements.txt -q
    log_info "Backend dependencies installed"
elif [ -f "backend/requirements.dev.txt" ]; then
    pip install -r backend/requirements.dev.txt -q
    log_info "Backend dev dependencies installed"
else
    log_warn "No requirements.txt found in backend/"
fi

# Install backend package in dev mode
if [ -d "backend" ]; then
    pip install -e backend/ -q 2>/dev/null || true
fi

# Frontend dependencies (if Node.js is available)
if command -v npm &> /dev/null; then
    if [ -d "frontend-dashboard" ]; then
        log_info "Installing frontend dependencies..."
        cd frontend-dashboard
        npm install 2>/dev/null || log_warn "npm install had issues"
        cd ..
        log_info "Frontend dependencies installed"
    fi
else
    log_warn "Node.js/npm not found — skipping frontend setup"
fi

# ---- 5. Install pre-commit hooks ----
log_info "Installing pre-commit hooks..."
if pip show pre-commit &> /dev/null; then
    pre-commit install
    log_info "Pre-commit hooks installed"
else
    pip install pre-commit -q
    pre-commit install
    log_info "Pre-commit hooks installed"
fi

# ---- 6. Set up environment variables ----
ENV_FILE=".env"
if [ ! -f "$ENV_FILE" ]; then
    log_info "Creating .env file..."
    cat > "$ENV_FILE" << 'EOF'
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/autobiz

# Debug
DEBUG=true
ENVIRONMENT=development

# JWT / Auth
JWT_SECRET=your-super-secret-jwt-key-change-me
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=60

# Redis
REDIS_URL=redis://localhost:6379

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# External APIs
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-your-anthropic-key
STRIPE_API_KEY=sk_test-your-stripe-key

# Email (Resend)
EMAIL_PROVIDER=resend
RESEND_API_KEY=re-your-resend-api-key
EMAIL_FROM=noreply@autobiz.ai

# Notifications
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/your/webhook
TWILIO_ACCOUNT_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-token
TWILIO_PHONE_NUMBER=+1234567890

# Infrastructure
RAILWAY_API_TOKEN=your-railway-token
FLY_API_TOKEN=your-fly-token
PINECONE_API_KEY=your-pinecone-key

# Sentry
SENTRY_DSN=

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1
EOF
    log_info ".env file created — please fill in your API keys!"
else
    log_info ".env file already exists"
fi

# ---- 7. Run database migrations ----
log_info "Running database migrations..."
if [ -f "backend/alembic.ini" ]; then
    cd backend
    alembic upgrade head 2>/dev/null || log_warn "Alembic migration had issues (may need DB running)"
    cd ..
elif [ -d "backend/migrations" ]; then
    log_info "Migrations directory found — run manually when DB is ready"
else
    log_warn "No Alembic migrations setup found"
fi

# ---- 8. Run linting and checks ----
log_info "Running initial lint checks..."
python3 -m flake8 backend/ --max-line-length=100 --ignore=E501,W503 || log_warn "Flake8 found issues (non-fatal)"
python3 -m black --check --line-length=100 backend/ || log_warn "Black formatting check failed (run: black backend/)"
python3 -m isort --check-only --profile black backend/ || log_warn "isort check failed (run: isort backend/)"

# If Ruff installed
if pip show ruff &> /dev/null; then
    ruff check . || log_warn "Ruff found issues"
fi

# ---- 9. Run tests ----
log_info "Running tests..."
if [ -d "backend/tests" ]; then
    cd backend
    python3 -m pytest tests/ -x -q --tb=short 2>/dev/null || log_warn "Some tests failed (expected on first setup)"
    cd ..
else
    log_warn "No tests directory found"
fi

# ---- Summary ----
echo ""
echo "========================================"
echo -e "  ${GREEN}Setup Complete!${NC}"
echo "========================================"
echo ""
echo "Quick start:"
echo "  1. Edit .env with your API keys"
echo "  2. Start database: docker compose up -d"
echo "  3. Run backend:    cd backend && uvicorn app.main:app --reload"
echo "  4. Run frontend:   cd frontend-dashboard && npm run dev"
echo ""
echo "Pre-commit hooks are installed."
echo "Run 'pre-commit run --all-files' to check all files."
echo "========================================"