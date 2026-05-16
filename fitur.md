# Fitur AutoBiz Engine

## 📦 Install & Setup

| # | Fitur | Status |
|---|-------|--------|
| 1 | Install lewat `curl -fsSL https://autobiz.ai/install.sh \| sh` | ✅ |
| 2 | Install lewat PowerShell `iwr -useb https://autobiz.ai/install.ps1 \| iex` | ✅ |
| 3 | Development shortcut `./autobiz` (auto Docker + venv + backend + TUI) | ✅ |
| 4 | `~/.autobiz/` folder struktur (app, venv, bin, .env) | ✅ |
| 5 | Auto-generate `.env` + `SECRET_KEY` | ✅ |
| 6 | Deteksi Docker — wajib, gak ada fallback | ✅ |
| 7 | Deteksi Python 3.9+ — install otomatis kalau gak ada | ✅ wrapper doang |

---

## 🔐 Auth & Security

| # | Fitur | Status |
|---|-------|--------|
| 8 | API Key auth (`ab_xxxx...`) — user masukin di TUI | ✅ |
| 9 | JWT auth — buat website integration | ✅ |
| 10 | Dual auth middleware — detek prefix `ab_` atau JWT | ✅ |
| 11 | `require_ceo()` — validasi role CEO beneran | ✅ |
| 12 | Role cuma 1: CEO (gak perlu multi-role) | ✅ |
| 13 | API Key CRUD — create, list, revoke lewat backend | ✅ |
| 14 | SECRET_KEY auto-generated, validasi startup | ✅ |
| 15 | Hardcoded password `secret` di DATABASE_URL — kena block validator kalau bukan localhost | ✅ |

---

## 🗄️ Database

| # | Fitur | Status |
|---|-------|--------|
| 16 | PostgreSQL — wajib, via Docker (`docker compose up -d db`) | ✅ |
| 17 | SQLite — **tidak ada fallback**, PostgreSQL atau gagal | ✅ |
| 18 | Auto `create_all()` tables di startup | ✅ |
| 19 | UUID type fix — convert string ↔ uuid.UUID untuk PostgreSQL compatibility | ✅ |
| 20 | Migrasi bisa via Alembic (udah ada folder `migrations/`) | ✅ skipping |

---

## 🧠 LLM & Agent System

| # | Fitur | Status |
|---|-------|--------|
| 21 | LLM Provider: OpenAI-compatible (bisa OpenRouter, Groq, vLLM, dll) | ✅ |
| 22 | LLM Provider: Ollama (lokal, auto-detect model) | ✅ |
| 23 | Pre-validasi LLM config sebelum create business | ✅ |
| 24 | Model capability classification (tiny/small/medium/large/xl) | ✅ |
| 25 | Agent warnings — kasi tau kalau model kurang gede buat agent tertentu | ✅ |
| 26 | Per-agent config: enabled, model_override, temperature | ✅ |
| 27 | API: `GET /api/v1/agents` — list agent + status + warnings | ✅ |
| 28 | API: `PUT /api/v1/agents/{name}/config` — update config | ✅ |
| 29 | API: `GET /api/v1/ollama/models` — list model Ollama + tier info | ✅ |
| 30 | API: `POST /api/v1/ollama/pull` — pull model Ollama | ✅ |

### Agent Roles

| Agent | Min Tier | Tugas |
|-------|----------|-------|
| Market Researcher | medium | Market analysis, competitor research, opportunity scoring |
| Software Engineer | large | Code generation, architecture design, technical planning |
| Brand Designer | medium | Brand identity, UI/UX planning, color schemes |
| Marketing Specialist | small | Campaign strategy, content creation, go-to-market |
| Finance Analyst | small | Pricing, financial projections, cost analysis |
| Customer Support | tiny | Ticket handling, FAQ responses, sentiment analysis |

---

## 🏭 Business Pipeline

| # | Fitur | Status |
|---|-------|--------|
| 31 | Create business dari ide → `POST /businesses/create` | ✅ |
| 32 | Pipeline: bikin 6 AgentTask + 1 ApprovalRequest | ✅ |
| 33 | Pipeline error → 500, bukan silent failed | ✅ |
| 34 | Business status: building → operating (via launch) | ✅ |
| 35 | Agent warnings di response create business | ✅ |
| 36 | List business, get detail, update, archive | ✅ |
| 37 | Timeline business (task history) | ✅ |

---

## ⚖️ Approvals

| # | Fitur | Status |
|---|-------|--------|
| 38 | List approval pending / all | ✅ |
| 39 | Approve tanpa alasan | ✅ |
| 40 | Reject **wajib alasan** ("Alasan wajib diisi saat menolak") | ✅ |
| 41 | Field `ceo_comments` — feedback dari CEO buat agent iterasi | ✅ |
| 42 | Approval auto-expire | ✅ via model |

---

## 📊 Monitoring & Health

| # | Fitur | Status |
|---|-------|--------|
| 43 | Health endpoint — return 503 kalau DB disconnected | ✅ |
| 44 | Health endpoint — return 200 kalau semua sehat | ✅ |
| 45 | `/settings/status` — cek DB, LLM, Ollama, Redis, agent warnings | ✅ |
| 46 | `/settings/env` — baca .env (secrets masked) | ✅ |
| 47 | `/settings/env` — save .env config | ✅ |
| 48 | `/settings/test-llm` — test koneksi LLM | ✅ |

---

## 🖥️ TUI (Terminal UI)

| # | Fitur | Status |
|---|-------|--------|
| 49 | Auth screen — input API Key | ✅ |
| 50 | Dashboard — stat cards + agent list + warnings | ✅ |
| 51 | Agent list — pilih agent → detail | ✅ |
| 52 | Agent detail — status, warning, config | ✅ |
| 53 | Bottom navigation — keyboard hints | ✅ |
| 54 | Dark mode — purple accent, #0a0e27 bg | ✅ |
| 55 | Status dots — ● optimal / ○ suboptimal | ✅ |
| 56 | **PROPER REDESIGN** — tiru style opencode/Claude Code | 🔄 Rich rewrite |

---

## 🌐 HTML Dashboard (WebView)

| # | Fitur | Status |
|---|-------|--------|
| 57 | Dashboard — `GET /ui/dashboard` | ✅ |
| 58 | Agent detail + config form | ✅ |
| 59 | CSS dark theme, grid layout, animations | ✅ |
| 60 | JS polling tiap 3 detik — update status realtime | ✅ |
| 61 | Live activity log | ✅ |

---

## 🐳 Docker

| # | Fitur | Status |
|---|-------|--------|
| 62 | PostgreSQL 16 Alpine — `docker compose up -d db` | ✅ |
| 63 | Redis 7 Alpine — `docker compose up -d redis` | ✅ |
| 64 | Volume persistent untuk PostgreSQL | ✅ |
| 65 | Healthcheck PostgreSQL + Redis | ✅ |
| 66 | Docker WAJIB — gak ada fallback ke SQLite | ✅ |

---

## ⚙️ Config (.env)

| Key | Default | Guna |
|-----|---------|------|
| `SECRET_KEY` | auto-generated | JWT signing |
| `DATABASE_URL` | `postgresql+psycopg2://autobiz:secret@localhost:5432/autobiz_engine` | DB koneksi |
| `LLM_PROVIDER` | `openai` | `openai` / `ollama` |
| `LLM_API_KEY` | `""` | API key LLM |
| `LLM_MODEL` | `gpt-4-turbo` | Model name |
| `LLM_BASE_URL` | `""` | Custom endpoint (OpenRouter, dll) |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama endpoint |
| `REDIS_URL` | `redis://localhost:6379` | Redis + Celery broker |
| `ENVIRONMENT` | `development` | `development` / `production` |
| `SENTRY_DSN` | `""` | Error tracking |

---

## 🗺️ Roadmap / Belum Dibuat

| # | Fitur | Prioritas |
|---|-------|-----------|
| A | **TUI redesign proper** (Rich, tiru opencode) | 🔴 HIGH |
| B | Business screen di TUI — list + create | 🟡 MEDIUM |
| C | Approvals screen di TUI — approve/reject | 🟡 MEDIUM |
| D | Settings screen di TUI — LLM config, .env editor | 🟡 MEDIUM |
| E | Agent config form di TUI — model override, temp, enabled | 🟡 MEDIUM |
| F | Website integration — register/login page | 🟢 LOW |
| G | API key management di website | 🟢 LOW |
| H | Agent skill system (custom prompt per user) | 🔘 NANTI |
| I | Multi-business dashboard | 🔘 NANTI |
| J | Export business as zip | 🔘 NANTI |
