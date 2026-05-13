# AutoBiz Engine — Deployment Guide

## Prerequisites

- Docker & Docker Compose ≥ v2.0
- Git
- A server with ≥ 4GB RAM, 2+ vCPUs (e.g., VPS, Railway, Fly.io)
- Domain name (optional, for HTTPS)

## Quick Start (Production)

### 1. Clone & Configure

```bash
git clone https://github.com/your-org/autobiz-engine.git
cd autobiz-engine

# Copy example env
cp .env.example .env
```

Edit `.env` with your secrets:

```env
# Database
DATABASE_URL=postgresql+psycopg2://user:password@db:5432/autobiz_engine
DB_USER=autobiz
DB_PASSWORD=your-strong-password

# Redis
REDIS_URL=redis://redis:6379

# Auth
SECRET_KEY=generate-a-strong-random-key

# OpenAI
OPENAI_API_KEY=sk-your-openai-key

# Anthropic (optional)
ANTHROPIC_API_KEY=sk-your-anthropic-key

# Email (Resend)
RESEND_API_KEY=re-your-resend-key

# Stripe (optional)
STRIPE_API_KEY=sk_live-your-stripe-key
STRIPE_WEBHOOK_SECRET=whsec-your-webhook-secret

# Monitoring (optional)
SENTRY_DSN=https://xxxx@sentry.io/123456
```

### 2. Build & Run

```bash
# Production (detached)
docker compose -f docker-compose.prod.yml up -d --build

# Development (with hot-reload)
docker compose up -d --build
```

### 3. Initialize Database

```bash
docker compose -f docker-compose.prod.yml exec backend python -m alembic upgrade head
```

Or for initial setup:

```bash
docker compose -f docker-compose.prod.yml exec backend python scripts/setup_db.py
```

### 4. Verify Deployment

```bash
# Health check
curl http://localhost:8000/health

# API root
curl http://localhost:8000/

# Prometheus metrics
curl http://localhost:8000/metrics
```

### 5. Seed Demo Data (Optional)

```bash
docker compose -f docker-compose.prod.yml exec backend python scripts/seed_demo_data.py
```

## Docker Images

| Service     | Build Context   | Port  |
|-------------|----------------|-------|
| Backend     | `./backend`    | 8000  |
| Frontend    | `./frontend-dashboard` | 3000 |
| Nginx       | `./nginx`      | 80/443|
| PostgreSQL  | postgres:16    | 5432  |
| Redis       | redis:7        | 6379  |

## Nginx Reverse Proxy

Nginx serves the frontend on port 80 and proxies `/api/*` to the backend.

Config: `nginx/nginx.conf`

## Running Workers

Celery workers are started automatically via docker-compose:

```bash
# Check worker status
docker compose -f docker-compose.prod.yml logs celery-worker

# Scale workers
docker compose -f docker-compose.prod.yml up -d --scale celery-worker=4
```

## Monitoring Setup

See `scripts/setup_monitoring.sh` for Prometheus + Grafana setup.

Default Grafana credentials: `admin / admin`

## Troubleshooting

- **Database connection refused**: Check `DATABASE_URL` in `.env` and ensure PostgreSQL health check passes
- **Redis errors**: Verify Redis is running: `docker compose logs redis`
- **Celery tasks stuck**: Restart worker: `docker compose restart celery-worker`
- **Out of memory**: Reduce `DATABASE_POOL_SIZE` in `.env`

## Updating

```bash
git pull origin main
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml exec backend python -m alembic upgrade head
```