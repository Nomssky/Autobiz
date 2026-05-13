# AutoBiz Engine — Troubleshooting Guide

## Common Issues & Solutions

---

### 🔴 Database Connection Errors

**Symptom:** `Connection refused` or `OperationalError` when starting the app.

**Solutions:**

1. **Check PostgreSQL is running:**
   ```bash
   docker compose -f docker-compose.prod.yml ps db
   ```

2. **Verify DATABASE_URL in `.env`:**
   ```env
   DATABASE_URL=postgresql+psycopg2://user:password@db:5432/autobiz_engine
   ```

3. **Wait for database health check:**
   ```bash
   docker compose -f docker-compose.prod.yml logs db
   # Wait for: "database system is ready to accept connections"
   ```

4. **Run migrations manually:**
   ```bash
   docker compose -f docker-compose.prod.yml exec backend python -m alembic upgrade head
   ```

---

### 🔴 Redis Connection Errors

**Symptom:** `Error 111 connecting to redis:6379. Connection refused.`

**Solutions:**

1. **Check Redis is running:**
   ```bash
   docker compose -f docker-compose.prod.yml ps redis
   ```

2. **Verify REDIS_URL:**
   ```env
   REDIS_URL=redis://redis:6379
   ```

3. **Test Redis manually:**
   ```bash
   docker compose -f docker-compose.prod.yml exec redis redis-cli ping
   # Should return: PONG
   ```

---

### 🟡 API Returns 401 Unauthorized

**Symptom:** All API calls return `401 Unauthorized`.

**Solutions:**

1. **Ensure Authorization header is set:**
   ```
   Authorization: Bearer <your-uuid-here>
   ```

2. **Check AuthMiddleware order** — it must be registered after CORS:
   ```python
   app.add_middleware(CORSMiddleware, ...)
   app.add_middleware(AuthMiddleware)
   ```

3. **Verify token format** — must be a valid UUID string.

---

### 🟡 Tasks Stuck in Queue

**Symptom:** Celery tasks remain in `pending` state indefinitely.

**Solutions:**

1. **Check Celery worker is running:**
   ```bash
   docker compose -f docker-compose.prod.yml logs celery-worker
   ```

2. **Restart workers:**
   ```bash
   docker compose -f docker-compose.prod.yml restart celery-worker
   ```

3. **Check Redis connectivity from worker:**
   ```bash
   docker compose -f docker-compose.prod.yml exec celery-worker redis-cli ping
   ```

4. **Scale workers if needed:**
   ```bash
   docker compose -f docker-compose.prod.yml up -d --scale celery-worker=4
   ```

---

### 🟡 High Response Times

**Symptom:** API responses are slow (>1 second).

**Diagnostic Steps:**

1. **Check X-Process-Time header** in response
2. **Review Prometheus metrics** at `/metrics`
3. **Check for N+1 queries:**
   ```python
   from app.infrastructure.query_optimizer import install_query_monitor, get_query_stats
   install_query_monitor(engine)
   # After requests:
   stats = get_query_stats()
   ```

4. **Common fixes:**
   - Ensure database indexes are applied (see `perf_indexes_v1` migration)
   - Enable Redis caching for frequent queries
   - Check if Gzip middleware is active

---

### 🟡 Health Check Failing

**Symptom:** `/health` returns `disconnected` or non-200 status.

**Solutions:**

1. **Check database connection:**
   ```bash
   docker compose -f docker-compose.prod.yml exec backend python scripts/healthcheck.py
   ```

2. **Check individual components:**
   ```bash
   # Database
   curl http://localhost:8000/health

   # Readiness
   curl http://localhost:8000/health/ready

   # Liveness (no DB check)
   curl http://localhost:8000/health/live
   ```

---

### 🔴 Docker Build Failures

**Symptom:** `docker compose build` fails with dependency errors.

**Solutions:**

1. **Clear Docker cache:**
   ```bash
   docker builder prune
   docker compose -f docker-compose.prod.yml build --no-cache
   ```

2. **Check Python version** — requires 3.11+

3. **Install system dependencies:**
   ```bash
   # For psycopg2
   apt-get install -y libpq-dev gcc
   ```

4. **Verify requirements.txt:**
   ```bash
   pip install -r backend/requirements.txt  # Test locally first
   ```

---

### 🟡 Load Testing Issues

**Symptom:** Locust errors or test failures.

**Solutions:**

1. **Install Locust:**
   ```bash
   pip install locust
   ```

2. **Start server before running tests:**
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 &
   ```

3. **Run with appropriate concurrency:**
   ```bash
   ./scripts/run_load_test.sh 50 5 60s
   # Users: 50, Spawn rate: 5/sec, Duration: 60s
   ```

4. **Check test DB is separate from production DB**

---

### 🔴 Monitoring Not Working

**Symptom:** `/metrics` returns 404 or empty.

**Solutions:**

1. **Verify PrometheusMiddleware is registered:**
   ```python
   from app.middleware.metrics import PrometheusMiddleware
   app.add_middleware(PrometheusMiddleware)
   ```

2. **Access metrics endpoint:**
   ```bash
   curl http://localhost:8000/metrics
   ```

3. **For Grafana dashboards**, run:
   ```bash
   bash scripts/setup_monitoring.sh
   ```

---

### 🅰️ Getting Help

If you encounter an issue not covered here:

1. Check logs: `docker compose logs -f`
2. Run health check: `python scripts/healthcheck.py`
3. Check application logs in `logs/` directory
4. Verify all environment variables are set correctly
5. Ensure all migrations are applied: `alembic upgrade head`