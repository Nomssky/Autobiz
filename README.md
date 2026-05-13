# AutoBiz Engine

An AI-powered platform for autonomously building and operating digital businesses autonomously.

## 🚀 Quick Start

```bash
# 1. Clone
git clone https://github.com/your-org/autobiz-engine.git
cd autobiz-engine

# 2. Configure environment
cp .env.example .env
# Edit .env with your secrets (see docs/DEPLOYMENT.md)

# 3. Start with Docker Compose
docker compose -f docker-compose.prod.yml up -d --build

# 4. Initialize database
docker compose -f docker-compose.prod.yml exec backend python -m alembic upgrade head

# 5. Verify
curl http://localhost:8000/health
```

## Project Structure

```
autobiz-engine/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── agents/             # AI agent implementations
│   │   ├── api/                # API routes & dependencies
│   │   ├── approval/           # CEO approval workflow
│   │   ├── infrastructure/     # Cache, DB, monitoring
│   │   ├── middleware/         # Request logging, Gzip, Prometheus
│   │   ├── models/             # SQLAlchemy models
│   │   ├── orchestrator/       # Multi-agent coordination
│   │   ├── schemas/            # Pydantic schemas
│   │   ├── tasks/              # Celery async tasks
│   │   └── config.py           # Settings
│   ├── migrations/             # Alembic migrations
│   ├── tests/                  # Test suite + load tests
│   │   └── load/               # Locust load tests
│   ├── Dockerfile              # Multi-stage build
│   └── requirements.txt
├── frontend-dashboard/         # Next.js dashboard
├── nginx/                      # Reverse proxy config
├── scripts/                    # Utilities
│   ├── healthcheck.py          # Health check script
│   ├── setup_db.py             # Initialize database
│   ├── seed_demo_data.py       # Demo data
│   ├── retrain_embeddings.py   # Vector DB updates
│   ├── run_load_test.sh        # Load test runner
│   └── setup_monitoring.sh     # Prometheus + Grafana
├── docs/                       # Documentation
│   ├── DEPLOYMENT.md           # Deployment guide
│   ├── API_REFERENCE.md        # Full API docs
│   ├── AGENT_GUIDE.md          # Agent customization
│   └── TROUBLESHOOTING.md      # Common issues
├── .github/workflows/
│   ├── ci.yml                  # CI: lint + test
│   └── deploy.yml              # CD: deploy to production
├── docker-compose.yml          # Development
├── docker-compose.prod.yml     # Production
├── docker-compose.monitoring.yml # Monitoring stack
└── README.md
```

## Key Features

- **Autonomous Business Building** — AI agents research, develop, design, market, and manage businesses
- **Multi-Agent Orchestration** — CrewAI-based hierarchical agent collaboration
- **Approval Workflow** — CEO approval system for major decisions
- **Real-time Dashboard** — Next.js frontend with live metrics
- **Scalable Architecture** — Celery workers, Redis caching, PostgreSQL
- **Production Ready** — Docker, CI/CD, monitoring, load tested

## Development

```bash
# Using docker-compose (recommended)
docker compose up -d

# Or run directly
cd backend
uvicorn app.main:app --reload --port 8000

# Run tests
python -m pytest tests/ -v

# Run load tests
bash scripts/run_load_test.sh 50 5 60s
```

## Production Deployment

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed instructions.

```bash
# Quick production deploy
docker compose -f docker-compose.prod.yml up -d --build

# Setup monitoring
bash scripts/setup_monitoring.sh
```

## Local Testing

```bash
# Unit tests
pytest tests/ -v --tb=short

# Load tests (requires server running)
pytest tests/load/test_scenarios.py -v

# Or use Locust directly
locust -f tests/load/locustfile.py --headless --users 50 --spawn-rate 5
```

## Current Sprint Progress

| Sprint | Status | Description |
|--------|--------|-------------|
| 1-9 | ✅ Complete | Core engine, agents, frontend, deployment |
| 10 | ✅ Complete | Load testing, performance optimization, monitoring |

See [plan.md](../plan.md) for full sprint breakdown.

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy, Celery, Redis, PostgreSQL
- **AI**: OpenAI GPT-4, Anthropic Claude, CrewAI, LangChain
- **Frontend**: Next.js, TailwindCSS, Zustand
- **Infrastructure**: Docker, Nginx, Prometheus, Grafana
- **CI/CD**: GitHub Actions

## License

Proprietary — AutoBiz Engine