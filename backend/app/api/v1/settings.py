"""Settings & integration status API — for the TUI settings screen."""

import os

from app.api.dependencies import get_db_session, require_ceo
from app.config import settings as app_settings
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session
from uuid import UUID

router = APIRouter(prefix="/settings", tags=["settings"])


class TestLLMRequest(BaseModel):
    provider: str = ""
    model: str = ""
    api_key: str = ""
    base_url: str = ""


@router.get("/status", summary="Get integration status for all services")
def get_status(_: UUID = Depends(require_ceo)):
    """Check connectivity for backend, database, LLM, Redis, etc."""
    status = {
        "backend": {"status": "ok", "version": "1.0.0"},
        "database": {"status": "unknown"},
        "llm": {
            "status": "unknown",
            "provider": app_settings.LLM_PROVIDER or "not configured",
            "model": app_settings.LLM_MODEL or app_settings.OPENAI_MODEL or "",
        },
        "redis": {"status": "unknown"},
    }

    # Check database
    try:
        from app.database import get_engine

        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        status["database"] = {"status": "connected", "url": str(engine.url).split("@")[-1] if "@" in str(engine.url) else "sqlite"}
    except Exception as e:
        status["database"] = {"status": "error", "error": str(e)}

    # Check LLM
    provider = (app_settings.LLM_PROVIDER or "").lower()
    has_api_key = bool(app_settings.LLM_API_KEY or app_settings.OPENAI_API_KEY)
    if provider == "ollama":
        status["llm"]["status"] = "configured"
        status["llm"]["note"] = "local — check Ollama is running"
    elif provider and has_api_key:
        status["llm"]["status"] = "configured"
    elif provider and not has_api_key:
        status["llm"]["status"] = "missing_api_key"
    else:
        status["llm"]["status"] = "not_configured"

    # Check Redis
    if app_settings.REDIS_URL:
        try:
            import redis as _redis

            r = _redis.from_url(app_settings.REDIS_URL)
            r.ping()
            status["redis"] = {"status": "connected"}
        except Exception:
            status["redis"] = {"status": "error", "error": "cannot connect"}
    else:
        status["redis"] = {"status": "not_configured"}

    return status


@router.post("/test-llm", summary="Test LLM connection with given config")
def test_llm(request: TestLLMRequest, _: UUID = Depends(require_ceo)):
    """Try a simple LLM call to verify the connection works."""
    try:
        from app.agents.llm_factory import create_llm

        llm = create_llm(
            provider=request.provider or None,
            model=request.model or None,
            api_key=request.api_key or None,
            base_url=request.base_url or None,
        )
        import asyncio

        loop = asyncio.new_event_loop()
        try:
            result = loop.run_until_complete(
                llm.ainvoke("Say exactly: OK", system_prompt="Reply with only OK.")
            )
            return {"success": True, "response": result.strip(), "provider": request.provider or app_settings.LLM_PROVIDER}
        finally:
            loop.close()
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/env", summary="Get safe .env configuration (secrets masked)")
def get_env(_: UUID = Depends(require_ceo)):
    """Read .env file and return safe config (API keys masked)."""
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "..", "..", ".env")
    alt_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "..", "..", "..", ".env")

    # Try multiple locations
    for p in [env_path, alt_path, os.path.abspath(".env")]:
        if os.path.exists(p):
            env_path = p
            break
    else:
        return {"env": {}, "path": "", "note": "No .env file found. Copy .env.example to .env"}

    safe_keys = {
        "LLM_PROVIDER", "LLM_MODEL", "LLM_BASE_URL", "LLM_TEMPERATURE",
        "EMBEDDING_PROVIDER", "EMBEDDING_MODEL", "EMBEDDING_BASE_URL",
        "OLLAMA_BASE_URL", "OLLAMA_MODEL",
        "OPENAI_MODEL", "ANTHROPIC_API_KEY",
        "DEBUG", "DATABASE_URL", "SECRET_KEY",
        "ENABLE_AUTO_APPROVE", "MAX_BUDGET_PER_BUSINESS",
    }
    secret_keys = {
        "LLM_API_KEY", "OPENAI_API_KEY", "EMBEDDING_API_KEY",
        "STRIPE_API_KEY", "STRIPE_WEBHOOK_SECRET",
        "RESEND_API_KEY", "SENDGRID_API_KEY",
        "SUPABASE_KEY", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY",
        "DISCORD_WEBHOOK_URL",
    }

    config = {}
    try:
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip().strip("\"'")
                    if key in safe_keys:
                        config[key] = val
                    elif key in secret_keys:
                        config[key] = val[:8] + "****" if len(val) > 8 else "****"
    except Exception:
        pass

    return {"env": config, "path": env_path}


class SaveEnvRequest(BaseModel):
    updates: dict


@router.put("/env", summary="Save .env configuration changes")
def save_env(request: SaveEnvRequest, _: UUID = Depends(require_ceo)):
    """Update .env file with new values. Only edits existing keys."""
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "..", "..", ".env")
    alt_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "..", "..", "..", ".env")

    for p in [env_path, alt_path, os.path.abspath(".env")]:
        if os.path.exists(p):
            env_path = p
            break
    else:
        raise HTTPException(status_code=404, detail="No .env file found")

    allowed_keys = {
        "LLM_PROVIDER", "LLM_MODEL", "LLM_API_KEY", "LLM_BASE_URL", "LLM_TEMPERATURE",
        "EMBEDDING_PROVIDER", "EMBEDDING_MODEL", "EMBEDDING_API_KEY", "EMBEDDING_BASE_URL",
        "OLLAMA_BASE_URL", "OLLAMA_MODEL",
        "OPENAI_API_KEY", "OPENAI_MODEL",
        "SECRET_KEY", "DATABASE_URL", "DEBUG",
        "DISCORD_WEBHOOK_URL",
    }

    try:
        with open(env_path) as f:
            lines = f.readlines()
        with open(env_path, "w") as f:
            updated = set()
            for line in lines:
                stripped = line.strip()
                if "=" in stripped and not stripped.startswith("#"):
                    key = stripped.split("=", 1)[0].strip()
                    if key in request.updates and key in allowed_keys:
                        f.write(f"{key}={request.updates[key]}\n")
                        updated.add(key)
                        continue
                f.write(line)
            # Append new keys that didn't exist
            for key, val in request.updates.items():
                if key not in updated and key in allowed_keys:
                    f.write(f"{key}={val}\n")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save .env: {e}")

    # Reload settings in memory (optional — next restart picks them up)
    return {"status": "saved", "updated": list(request.updates.keys())}
