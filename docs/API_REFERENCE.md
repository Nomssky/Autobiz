# AutoBiz Engine — API Reference

Base URL: `http://localhost:8000/api/v1`

All endpoints require Bearer token authentication in the `Authorization` header.

## Authentication

All requests must include:
```
Authorization: Bearer <your-uuid>
```

## Businesses

### Create Business
```
POST /api/v1/businesses/create
```
**Request Body:**
```json
{
  "idea": "AI-powered SaaS platform",
  "ceo_id": "uuid-string"
}
```
**Response (201):**
```json
{
  "id": "uuid",
  "name": "AI-powered SaaS platform",
  "description": "AI-powered SaaS platform",
  "status": "building",
  "current_phase": "initialization",
  "ceo_id": "uuid",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

### List Businesses
```
GET /api/v1/businesses/?status=building&ceo_id=uuid&skip=0&limit=50
```
**Response (200):**
```json
[
  {
    "id": "uuid",
    "name": "TestCo",
    "status": "building",
    "current_phase": "initialization",
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```

### Get Business
```
GET /api/v1/businesses/{business_id}
```
**Response (200):** `BusinessResponse` object

### Update Business
```
PATCH /api/v1/businesses/{business_id}
```
**Request Body:**
```json
{
  "name": "Updated Name",
  "description": "New description"
}
```
**Response (200):** Updated `BusinessResponse`

### Archive Business
```
DELETE /api/v1/businesses/{business_id}
```
**Response (204):** No content

### Launch Business
```
POST /api/v1/businesses/{business_id}/launch
```
**Response (200):** Updated `BusinessResponse`

### Get Business Timeline
```
GET /api/v1/businesses/{business_id}/timeline
```
**Response (200):**
```json
{
  "business_id": "uuid",
  "phases": [
    {
      "task_id": "uuid",
      "role_name": "researcher",
      "task_type": "market_analysis",
      "status": "completed",
      "priority": 3,
      "created_at": "2024-01-01T00:00:00Z",
      "completed_at": "2024-01-01T00:05:00Z"
    }
  ]
}
```

## Metrics

### List Metrics
```
GET /api/v1/metrics/?business_id=uuid&recorded_by_role=finance&skip=0&limit=50
```
**Response (200):** Array of `MetricSnapshotResponse`

### Get Metric
```
GET /api/v1/metrics/{metric_id}
```

### Get Real-Time Metrics
```
GET /api/v1/metrics/{business_id}/realtime
```
**Response (200):**
```json
{
  "current": {
    "revenue": 1450.75,
    "users": 342,
    "active_users": 278,
    "bugs": 3,
    "support_tickets": 12
  },
  "trends": {
    "revenue_growth": 0.0,
    "user_growth": 0.0,
    "churn_rate": 0.028
  },
  "alerts": [
    {"type": "warning", "message": "High bug count detected"}
  ]
}
```

### Get Metric Summary
```
GET /api/v1/metrics/{business_id}/summary?days=7
```

### Create Metric Snapshot
```
POST /api/v1/metrics/
```

### Delete Metric
```
DELETE /api/v1/metrics/{metric_id}
```

## Approvals

### List Approvals
```
GET /api/v1/approvals/?status_filter=pending&business_id=uuid&skip=0&limit=50
```

### Get Pending Approvals
```
GET /api/v1/approvals/pending?business_id=uuid&limit=50
```

### Get Approval
```
GET /api/v1/approvals/{approval_id}
```

### Create Approval Request
```
POST /api/v1/approvals/
```

### Submit Decision
```
POST /api/v1/approvals/{approval_id}/decide
```
**Request Body:**
```json
{
  "decision": "approve",
  "comments": "Looks good, proceed with implementation"
}
```

### Update Approval
```
PATCH /api/v1/approvals/{approval_id}
```

### Cancel Approval
```
DELETE /api/v1/approvals/{approval_id}
```

## Health Endpoints

No authentication required.

```
GET /          → {"message": "AutoBiz Engine API is running"}
GET /health    → {"status": "healthy", "database": "connected"}
GET /health/ready → {"status": "ready"}
GET /health/live  → {"status": "alive"}
GET /metrics      → Prometheus metrics (text format)
```

## Error Responses

All errors follow this format:
```json
{
  "error": "Error Type",
  "detail": "Detailed error message"
}
```

| Status Code | Meaning |
|-------------|---------|
| 400 | Bad Request — validation error |
| 401 | Unauthorized — missing or invalid token |
| 403 | Forbidden — insufficient permissions |
| 404 | Not Found — resource doesn't exist |
| 500 | Internal Server Error — server-side failure |