# AutoBiz Engine

AI-powered platform for autonomously building and operating digital businesses.

## Quick Start

```bash
git clone https://github.com/Nomssky/Autobiz.git
cd Autobiz

cp .env.example .env
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head

curl http://localhost:8000/health
```

## Project Structure

```
├── backend/                    # FastAPI + Celery
│   ├── app/
│   │   ├── agents/             # 6 AI agents + Pydantic output schemas
│   │   ├── api/v1/             # businesses, approvals, metrics, billing, api-keys, webhooks
│   │   ├── approval/           # CEO approval gateway + Discord/Email/SMS notifier
│   │   ├── infrastructure/     # Code sandbox, deploy manager, vector store, cache
│   │   ├── middleware/         # Logging, Gzip, Prometheus, Rate limit, Audit
│   │   ├── models/             # 11 SQLAlchemy models (+ subscription, org, audit)
│   │   ├── orchestrator/       # Multi-agent pipeline orchestration
│   │   └── auth/               # JWT handler + middleware
│   ├── migrations/             # Alembic (initial + perf indexes + multi-tenancy)
│   ├── tests/                  # 78 tests (unit + integration + load)
│   └── requirements.txt
├── frontend-dashboard/         # Next.js 14 dashboard
├── monitoring/                 # Grafana dashboard + Prometheus alerts
├── nginx/                      # Reverse proxy
├── scripts/                    # healthcheck, seed, setup, load test
├── docs/                       # Deployment, API, Agent, Troubleshooting
└── docker-compose*.yml         # Dev, Production, Monitoring
```

## Features

| Area | Capabilities |
|------|-------------|
| **AI Agents** | Researcher, Developer, Designer, Marketer, Finance, Support |
| **Approval Workflow** | CEO approve/reject, Discord/Email/SMS notifications, auto-approval rules |
| **Subscription** | Starter/Growth/Enterprise tiers, Stripe integration, usage metering |
| **Multi-Tenancy** | Organizations, role-based access (owner/admin/viewer), API keys, audit log |
| **Monitoring** | Prometheus metrics, Grafana dashboard (12 panels + alerts), Sentry |
| **Infrastructure** | Docker sandbox, Railway/Fly.io deploy manager, Pinecone/Qdrant vector store |

## Quick Commands

```bash
# Run tests
cd backend && python -m pytest tests/ -v --tb=short

# Seed demo data
python scripts/seed_demo_data.py

# Load test
bash scripts/run_load_test.sh 50 5 60s

# Monitoring
bash scripts/setup_monitoring.sh
# Grafana: http://localhost:3001 (admin/admin)
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/businesses/create` | Create business from idea |
| `GET` | `/api/v1/businesses/` | List businesses |
| `GET/POST` | `/api/v1/approvals/` | CRUD approval requests |
| `POST` | `/api/v1/approvals/{id}/decide` | CEO approve/reject |
| `GET` | `/api/v1/metrics/{id}/realtime` | Real-time metrics |
| `GET` | `/api/v1/billing/usage` | AI budget usage |
| `GET/POST/DELETE` | `/api/v1/api-keys/` | API key management |
| `POST` | `/api/v1/webhooks/stripe/*` | Stripe event handlers |

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy, Celery, Redis, PostgreSQL
- **AI**: OpenAI GPT-4, Anthropic Claude, CrewAI, LangChain
- **Frontend**: Next.js 14, TailwindCSS, Zustand, Recharts
- **Infra**: Docker, Nginx, Prometheus, Grafana, GitHub Actions

## Documentation

- [Deployment Guide](docs/DEPLOYMENT.md)
- [API Reference](docs/API_REFERENCE.md)
- [Agent Customization](docs/AGENT_GUIDE.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
