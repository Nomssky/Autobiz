# AutoBiz Engine — TUI Design Document

## Apa Itu AutoBiz Engine?

AutoBiz Engine adalah AI-powered platform untuk membangun dan mengoperasikan bisnis digital secara otonom. User (CEO) cukup memberikan ide bisnis, lalu sistem akan mengorkestrasi tim AI agent (Researcher, Developer, Designer, Marketer, Finance, Support) untuk meneliti, membangun, mendesain, memasarkan, dan mengelola keuangan bisnis tersebut.

## Arsitektur

```
┌─────────────────────────────────────────────────┐
│                   TUI (Go/Bubbletea)             │
│  ┌───────────┬──────────┬──────────┬──────────┐ │
│  │ Dashboard │Businesses│Approvals │ Metrics  │ │
│  └───────────┴──────────┴──────────┴──────────┘ │
│                    │ HTTP REST                    │
└────────────────────┼────────────────────────────┘
                     ▼
┌──────────────────────────────────────────────────┐
│           Backend (Python/FastAPI)                │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐  │
│  │ Auth │ │ Biz  │ │Approval│ │Metrics│ │Agent │  │
│  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘  │
│                    │ SQLAlchemy                   │
│              ┌─────┴─────┐                       │
│              │  SQLite/  │                       │
│              │PostgreSQL │                       │
│              └───────────┘                       │
└──────────────────────────────────────────────────┘
```

## User Flow

```
Start → Login/Register → Dashboard
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
         Businesses    Approvals      Metrics
              │             │             │
    ┌─────────┼──┐    ┌─────┴─────┐       │
    ▼         ▼  ▼    ▼           ▼       ▼
  List    Create Detail Approve  Reject  View Stats
```

## Backend API Endpoints

Base URL: `http://localhost:8000/api/v1`

### Auth

| Method | Path | Body | Response | Notes |
|--------|------|------|----------|-------|
| POST | `/auth/register` | `{email, password, name}` | `{access_token, token_type, user_id, email, name, role}` | Buat akun baru |
| POST | `/auth/login` | `{email, password}` | `{access_token, token_type, user_id, email, name, role}` | Login |

### Businesses

| Method | Path | Body/Params | Response | Notes |
|--------|------|-------------|----------|-------|
| GET | `/businesses/` | `?status=&skip=&limit=` | `[{id, name, description, status, current_phase, created_at, updated_at}]` | List semua bisnis |
| POST | `/businesses/create` | `{idea}` | `{id, name, status, ...}` | Buat bisnis baru dari ide |
| GET | `/businesses/{id}` | — | `{id, name, status, current_phase, ceo_id, ...}` | Detail bisnis |
| PATCH | `/businesses/{id}` | `{name?, status?, ...}` | `{id, name, ...}` | Update bisnis |
| DELETE | `/businesses/{id}` | — | 204 | Arsipkan bisnis |
| POST | `/businesses/{id}/launch` | — | `{id, status: "operating", ...}` | Launch bisnis |
| GET | `/businesses/{id}/timeline` | — | `{phases: [{role_name, task_type, status, ...}]}` | Timeline agent tasks |

### Approvals

| Method | Path | Body | Response | Notes |
|--------|------|------|----------|-------|
| GET | `/approvals/` | `?status=&business_id=` | `[{id, title, status, urgency, ...}]` | List approvals |
| GET | `/approvals/pending` | — | `[{id, title, urgency, created_at, ...}]` | Pending approvals saja |
| POST | `/approvals/` | `{business_id, title, description, proposed_changes, urgency}` | `{id, status: "pending", ...}` | Buat approval request |
| POST | `/approvals/{id}/decide` | `{decision: "approve"|"reject", ceo_id, comments?}` | `{approved: bool, message}` | CEO decide |
| PATCH | `/approvals/{id}` | `{title?, description?, ...}` | `{id, ...}` | Update approval |
| DELETE | `/approvals/{id}` | — | 204 | Cancel approval |

### Metrics

| Method | Path | Body/Params | Response | Notes |
|--------|------|-------------|----------|-------|
| GET | `/metrics/` | `?business_id=&skip=&limit=` | `[{id, business_id, recorded_by_role, daily_revenue, users_count, churn_rate, created_at}]` | List metrics |
| POST | `/metrics/` | `{business_id, recorded_by_role, daily_revenue?, users_count?, churn_rate?, ...}` | `{id, ...}` | Record metric |
| GET | `/metrics/{id}` | — | `{id, ...}` | Detail metric |
| GET | `/metrics/{id}/realtime` | — | `{current: {...}, trends: {...}, alerts: [...]}` | Realtime metrics |
| GET | `/metrics/{id}/summary` | `?days=` | `{snapshot_count, avg_daily_revenue, avg_users, ...}` | Summary |

### Vectors (Knowledge)

| Method | Path | Body | Response | Notes |
|--------|------|------|----------|-------|
| POST | `/vectors/search` | `{business_id, query, top_k?}` | `{query, results: [{id, score, payload}]}` | Semantic search |
| POST | `/vectors/upsert` | `{vectors: [{id, vector, payload}]}` | `{upserted_count}` | Insert vectors |
| GET | `/vectors/{business_id}/knowledge` | — | `[{source, content, role}]` | Knowledge entries |
| GET | `/vectors/stats` | — | `{total_vectors, backend, collection}` | Vector store stats |

### Learning

| Method | Path | Body | Response | Notes |
|--------|------|------|----------|-------|
| POST | `/learning/feedback` | `{business_id, content, feedback_type?, sentiment_score?}` | `{feedback_id, status, learning_actions}` | Submit feedback |
| GET | `/learning/evaluation/{business_id}` | `?role=&days=` | `{overall_score, evaluations: [...]}` | Agent evaluation |
| GET | `/learning/suggestions/{business_id}` | `?role=&days=` | `{suggestions: [...]}` | Improvement suggestions |
| POST | `/learning/optimize-prompt` | `{business_id, role_name, original_prompt}` | `{original, optimized, ...}` | Optimize prompt |

### Billing

| Method | Path | Body | Response | Notes |
|--------|------|------|----------|-------|
| GET | `/billing/usage` | — | `{tier, subscription_status, usage: {...}, limits: {...}}` | Current usage |
| POST | `/billing/upgrade` | `?tier=` | `{url?, type?}` | Upgrade subscription |
| POST | `/billing/create-portal-session` | `{business_id}` | `{url}` | Stripe customer portal |

---

## TUI Screens

### 1. Auth Screen (Login/Register)

**State:** Sebelum user login

```
┌─────────────────────────────────────┐
│         AutoBiz Engine              │
│                                     │
│  Email:                             │
│  █                                  │
│                                     │
│  Enter: next • Backspace: delete    │
│  Ctrl+C: quit                       │
└─────────────────────────────────────┘
```

Flow: Email → Password → Name (kosongkan untuk login) → Submit

### 2. Dashboard (Tab 1)

**State:** Sesudah login, tab default

```
┌─────────────────────────────────────┐
│  AutoBiz Engine | user@email.com    │
│ ┌──────────┬──────────┬──────────┐  │
│ │1:Dashboard│2:Business │3:Approval│ │
│ └──────────┴──────────┴──────────┘  │
│ ┌─────────────────────────────┐     │
│ │ Welcome to AutoBiz Engine   │     │
│ │                             │     │
│ │ ┌──────┐ ┌──────┐ ┌──────┐ │     │
│ │ │ Biz  │ │Approval│ │Metrics││     │
│ │ │  3   │ │   2   │ │   5  │ │     │
│ │ └──────┘ └──────┘ └──────┘ │     │
│ │                             │     │
│ │ ⚠ 2 pending approval(s)    │     │
│ │                             │     │
│ │ Press 1-4 to switch tabs    │     │
│ └─────────────────────────────┘     │
└─────────────────────────────────────┘
```

**Tombol:** `1-4` ganti tab, `n` create business, `q` quit

### 3. Businesses List (Tab 2 — List Mode)

```
┌─────────────────────────────────────┐
│  AutoBiz Engine | user@email.com    │
│ ┌──────────┬──────────┬──────────┐  │
│ │1:Dashboard│2:Business│3:Approval│ │
│ └──────────┴──────────┴──────────┘  │
│ ┌─────────────────────────────┐     │
│ │ Businesses                  │     │
│ │                             │     │
│ │ ▸ AI SaaS Platform building │     │
│ │   E-commerce Store  design  │     │
│ │   Chatbot Service  research │     │
│ │                             │     │
│ │ ↑↓: navigate • enter: detail│     │
│ │ n: new • r: refresh • q:quit│     │
│ └─────────────────────────────┘     │
└─────────────────────────────────────┘
```

**Tombol:** `↑↓`/`jk` navigasi, `enter` detail, `n` create, `r` refresh, `q` quit

### 4. Create Business (Tab 2 — Create Mode)

```
┌─────────────────────────────────────┐
│  AutoBiz Engine | user@email.com    │
│ ┌──────────┬──────────┬──────────┐  │
│ │1:Dashboard│2:Business│3:Approval│ │
│ └──────────┴──────────┴──────────┘  │
│ ┌─────────────────────────────┐     │
│ │ New Business                │     │
│ │                             │     │
│ │ Describe your business idea:│     │
│ │ AI-powered SaaS for █       │     │
│ │                             │     │
│ │ Enter: create • Esc: back   │     │
│ └─────────────────────────────┘     │
└─────────────────────────────────────┘
```

**Tombol:** `enter` create, `Esc` back

### 5. Business Detail (Tab 2 — Detail Mode)

```
┌─────────────────────────────────────┐
│  AutoBiz Engine | user@email.com    │
│ ┌──────────┬──────────┬──────────┐  │
│ │1:Dashboard│2:Business│3:Approval│ │
│ └──────────┴──────────┴──────────┘  │
│ ┌─────────────────────────────┐     │
│ │ AI SaaS Platform            │     │
│ │                             │     │
│ │ ID:     abc123-...          │     │
│ │ Status: building            │     │
│ │ Phase:  design              │     │
│ │ Created: 2026-05-14         │     │
│ │                             │     │
│ │ Esc: back                   │     │
│ └─────────────────────────────┘     │
└─────────────────────────────────────┘
```

**Tombol:** `Esc`/`q` back

### 6. Approvals (Tab 3)

```
┌─────────────────────────────────────┐
│  AutoBiz Engine | user@email.com    │
│ ┌──────────┬──────────┬──────────┐  │
│ │1:Dashboard│2:Business│3:Approval│ │
│ └──────────┴──────────┴──────────┘  │
│ ┌─────────────────────────────┐     │
│ │ Approvals                   │     │
│ │                             │     │
│ │ ▸ Marketing Budget  HIGH    │     │
│ │   Design Approval  normal   │     │
│ │                             │     │
│ │ ← → navigate               │     │
│ │ a: approve • r: reject     │     │
│ │ enter: toggle detail       │     │
│ └─────────────────────────────┘     │
└─────────────────────────────────────┘
```

**Tombol:** `↑↓`/`jk` navigasi, `a` approve, `r` reject, `enter` toggle detail

### 7. Metrics (Tab 4)

```
┌─────────────────────────────────────┐
│  AutoBiz Engine | user@email.com    │
│ ┌──────────┬──────────┬──────────┐  │
│ │1:Dashboard│2:Business│3:Approval│ │
│ └──────────┴──────────┴──────────┘  │
│ ┌─────────────────────────────┐     │
│ │ Metrics                     │     │
│ │                             │     │
│ │ finance                     │     │
│ │   Revenue:    $1,450.75     │     │
│ │   Users:      342           │     │
│ │   Churn Rate: 2.8%          │     │
│ │   2026-05-14                │     │
│ │                             │     │
│ │ r: refresh • q: quit        │     │
│ └─────────────────────────────┘     │
└─────────────────────────────────────┘
```

**Tombol:** `r` refresh

---

## TUI Component Tree

```
App
├── AuthScreen (stateLogin / stateRegister)
│   ├── EmailInput
│   ├── PasswordInput
│   └── NameInput (opsional, untuk register)
│
└── DashboardScreen (stateDashboard)
    ├── Header
    │   └── Title + UserEmail
    ├── TabBar
    │   ├── TabDashboard
    │   ├── TabBusinesses
    │   ├── TabApprovals
    │   └── TabMetrics
    └── ContentPanel
        ├── DashboardHome
        │   ├── StatCard (Businesses count)
        │   ├── StatCard (Pending Approvals)
        │   └── StatCard (Metrics count)
        ├── BusinessesView
        │   ├── BusinessList (pageList)
        │   │   ├── BusinessItem (selected dengan ▸)
        │   │   └── EmptyState
        │   ├── CreateBusiness (pageCreate)
        │   │   └── IdeaInput
        │   └── BusinessDetail (pageDetail)
        ├── ApprovalsView
        │   ├── ApprovalList
        │   │   └── ApprovalItem (selected dengan ▸)
        │   └── EmptyState
        └── MetricsView
            └── MetricList
```

## Color Palette

| Token | Dark Color | Penggunaan |
|-------|-----------|------------|
| `subtle` | `#383838` | Border, separator |
| `highlight` | `#7B59E0` | Active tab border, selected item |
| `special` | `#73F59F` | Success, stat card accent |
| `warn` | `#E06C75` | Error, high urgency, reject |
| `info` | `#61AFEF` | Info text, metric labels |

## Key Bindings

| Key | Screen | Action |
|-----|--------|--------|
| `1-4` | Dashboard | Switch tabs |
| `↑` / `k` | Lists | Navigate up |
| `↓` / `j` | Lists | Navigate down |
| `enter` | Lists | Select/detail |
| `enter` | Auth | Next field / submit |
| `n` | Dashboard/Biz | Create new business |
| `a` | Approvals | Approve selected |
| `r` | Approvals | Reject selected |
| `r` | Metrics | Refresh |
| `Esc` | Any | Back to previous screen |
| `q` / `Ctrl+C` | Any | Quit |
| `backspace` | Input | Delete character |
