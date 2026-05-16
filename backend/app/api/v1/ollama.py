import logging

import httpx
from app.agents.registry import classify_model
from app.api.dependencies import require_ceo
from app.config import settings
from fastapi import APIRouter, Depends, HTTPException
from uuid import UUID

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ollama", tags=["ollama"])


@router.get("/models", summary="List available Ollama models")
def list_models(_: UUID = Depends(require_ceo)):
    """List all models available in the local Ollama instance."""
    base_url = (settings.OLLAMA_BASE_URL or "http://localhost:11434").rstrip("/")
    try:
        resp = httpx.get(f"{base_url}/api/tags", timeout=5.0)
        resp.raise_for_status()
        data = resp.json()
        models = []
        for m in data.get("models", []):
            model_name = m["name"]
            info = classify_model(model_name)
            models.append({
                "name": model_name,
                "tier": info["tier"],
                "params": info["params"],
            })
        return {"models": sorted(models, key=lambda x: x["name"]), "status": "available"}
    except httpx.ConnectError:
        return {"models": [], "status": "not_running", "error": "Cannot connect to Ollama"}
    except Exception as e:
        logger.warning(f"Failed to list Ollama models: {e}")
        return {"models": [], "status": "error", "error": str(e)}


@router.post("/pull", summary="Pull an Ollama model")
def pull_model(model: str, _: UUID = Depends(require_ceo)):
    """Pull a model in Ollama (runs in background)."""
    base_url = (settings.OLLAMA_BASE_URL or "http://localhost:11434").rstrip("/")
    try:
        resp = httpx.post(f"{base_url}/api/pull", json={"name": model}, timeout=300.0)
        resp.raise_for_status()
        return {"status": "pulling", "model": model}
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Ollama is not running")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
