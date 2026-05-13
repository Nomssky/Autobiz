#!/usr/bin/env bash
# run_load_test.sh — Automation script for running Locust load tests
# Usage: ./scripts/run_load_test.sh [num_users] [spawn_rate] [run_time]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

NUM_USERS=${1:-50}
SPAWN_RATE=${2:-5}
RUN_TIME=${3:-60s}
HOST=${4:-http://localhost:8000}

echo "========================================"
echo "  AutoBiz Engine — Load Test Runner"
echo "========================================"
echo "  Users:      $NUM_USERS"
echo "  Spawn rate: $SPAWN_RATE users/sec"
echo "  Duration:   $RUN_TIME"
echo "  Host:       $HOST"
echo "========================================"

# Check if locust is installed
if ! command -v locust &> /dev/null; then
    echo "❌ Locust not found. Installing..."
    pip install locust
fi

# Check if server is running
echo ""
echo "📡 Checking if server is running at $HOST..."
if curl -s --max-time 5 "$HOST/health" | grep -q "healthy\|connected"; then
    echo "✅ Server is healthy"
else
    echo "⚠️  Server may not be running at $HOST"
    echo "   Make sure to start the server first:"
    echo "   uvicorn app.main:app --host 0.0.0.0 --port 8000"
    echo ""
    read -p "Continue anyway? (y/N): " confirm
    if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
        echo "Aborted."
        exit 1
    fi
fi

echo ""
echo "🚀 Starting headless load test..."
echo ""

# Run locust in headless mode
locust \
    -f tests/load/locustfile.py \
    --headless \
    --users "$NUM_USERS" \
    --spawn-rate "$SPAWN_RATE" \
    --run-time "$RUN_TIME" \
    --host "$HOST" \
    --html reports/load_test_report.html \
    --csv reports/load_test_stats \
    2>&1 | tee reports/load_test_output.log

echo ""
echo "========================================"
echo "  Load test complete!"
echo "  Report: reports/load_test_report.html"
echo "  Stats:  reports/load_test_stats_stats.csv"
echo "========================================"

# Run concurrent scenario tests
echo ""
echo "📊 Running concurrent scenario tests..."
python -m pytest tests/load/test_scenarios.py -v --tb=short 2>&1 | tee reports/concurrent_test_output.log

echo ""
echo "✅ All load tests completed!"