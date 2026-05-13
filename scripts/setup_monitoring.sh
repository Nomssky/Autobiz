#!/usr/bin/env bash
# setup_monitoring.sh — Deploy Prometheus + Grafana for AutoBiz Engine
# Usage: bash scripts/setup_monitoring.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

echo "=========================================="
echo "  AutoBiz Engine — Monitoring Setup"
echo "=========================================="

# ---- Configuration ----
PROMETHEUS_PORT=${PROMETHEUS_PORT:-9090}
GRAFANA_PORT=${GRAFANA_PORT:-3000}
GRAFANA_ADMIN_USER=${GRAFANA_ADMIN_USER:-admin}
GRAFANA_ADMIN_PASS=${GRAFANA_ADMIN_PASS:-admin}

# ---- Check Docker ----
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

echo ""
echo "📦 Setting up Prometheus + Grafana..."

# ---- Create monitoring directories ----
mkdir -p monitoring/prometheus
mkdir -p monitoring/grafana/dashboards
mkdir -p monitoring/grafana/provisioning/dashboards
mkdir -p monitoring/grafana/provisioning/datasources

# ---- Prometheus Config ----
cat > monitoring/prometheus/prometheus.yml << 'PROMETHEUS'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'autobiz-api'
    static_configs:
      - targets: ['host.docker.internal:8000']
    metrics_path: '/metrics'
    scrape_interval: 10s

  - job_name: 'celery-worker'
    static_configs:
      - targets: ['host.docker.internal:9808']
    metrics_path: '/metrics'

  - job_name: 'postgresql'
    static_configs:
      - targets: ['host.docker.internal:9187']
    metrics_path: '/metrics'

  - job_name: 'redis'
    static_configs:
      - targets: ['host.docker.internal:9121']
    metrics_path: '/metrics'
PROMETHEUS

echo "✅ Prometheus config created"

# ---- Grafana Dashboard ----
cat > monitoring/grafana/dashboards/autobiz_dashboard.json << 'GRAFANA'
{
  "dashboard": {
    "id": null,
    "uid": "autobiz-engine",
    "title": "AutoBiz Engine Dashboard",
    "tags": ["autobiz", "production"],
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "title": "HTTP Requests / min",
        "type": "graph",
        "targets": [{
          "expr": "rate(http_requests_total[5m]) * 60",
          "legendFormat": "{{method}}"
        }],
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0}
      },
      {
        "id": 2,
        "title": "Request Duration (p95)",
        "type": "graph",
        "targets": [{
          "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
          "legendFormat": "{{method}}"
        }],
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0}
      },
      {
        "id": 3,
        "title": "Active Requests",
        "type": "stat",
        "targets": [{
          "expr": "http_requests_in_progress"
        }],
        "gridPos": {"h": 4, "w": 6, "x": 0, "y": 8}
      },
      {
        "id": 4,
        "title": "Total Errors",
        "type": "stat",
        "targets": [{
          "expr": "rate(http_errors_total[5m])"
        }],
        "gridPos": {"h": 4, "w": 6, "x": 6, "y": 8}
      },
      {
        "id": 5,
        "title": "Business Creations / hour",
        "type": "graph",
        "targets": [{
          "expr": "rate(http_requests_total{method=\"POST /api/v1/businesses/create\"}[1h]) * 3600"
        }],
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 12}
      },
      {
        "id": 6,
        "title": "Top Slow Endpoints",
        "type": "table",
        "targets": [{
          "expr": "topk(10, avg by(method) (rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m])))"
        }],
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 12}
      }
    ],
    "time": {"from": "now-1h", "to": "now"},
    "refresh": "30s"
  }
}
GRAFANA

echo "✅ Grafana dashboard created"

# ---- Grafana Datasource Provisioning ----
cat > monitoring/grafana/provisioning/datasources/prometheus.yml << 'DATASOURCE'
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
DATASOURCE

# ---- Grafana Dashboard Provisioning ----
cat > monitoring/grafana/provisioning/dashboards/dashboards.yml << 'DASHBOARD'
apiVersion: 1
providers:
  - name: 'Default'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 30
    options:
      path: /etc/grafana/provisioning/dashboards
      foldersFromFilesStructure: false
DASHBOARD

# ---- Docker Compose for Monitoring ----
cat > docker-compose.monitoring.yml << MONITORING
services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "${PROMETHEUS_PORT}:9090"
    volumes:
      - ./monitoring/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    ports:
      - "${GRAFANA_PORT}:3000"
    environment:
      - GF_SECURITY_ADMIN_USER=${GRAFANA_ADMIN_USER}
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASS}
    volumes:
      - ./monitoring/grafana/provisioning:/etc/grafana/provisioning
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
      - grafana_data:/var/lib/grafana
    restart: unless-stopped

volumes:
  grafana_data:
MONITORING

echo "✅ Docker Compose monitoring file created"

# ---- Summary ----
echo ""
echo "=========================================="
echo "  Monitoring setup complete!"
echo "=========================================="
echo ""
echo "Access:"
echo "  Prometheus:  http://localhost:${PROMETHEUS_PORT}"
echo "  Grafana:     http://localhost:${GRAFANA_PORT} (admin/admin)"
echo ""
echo "To start monitoring:"
echo "  docker compose -f docker-compose.monitoring.yml up -d"
echo ""
echo "To stop monitoring:"
echo "  docker compose -f docker-compose.monitoring.yml down"
echo ""

# Ask if user wants to start monitoring now
read -p "Start monitoring now? (y/N): " confirm
if [[ "$confirm" == "y" || "$confirm" == "Y" ]]; then
    docker compose -f docker-compose.monitoring.yml up -d
    echo ""
    echo "✅ Monitoring is running!"
    echo "   Wait ~30 seconds for first data points."
fi