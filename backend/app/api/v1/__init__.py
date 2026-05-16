from app.api.v1 import (
    agents,
    api_keys,
    approvals,
    auth,
    businesses,
    learning,
    metrics,
    ollama,
    settings,
    vectors,
    webhooks,
)
from app.api.v1.ui import router as ui_router
from fastapi import APIRouter

router = APIRouter()

router.include_router(agents.router)
router.include_router(auth.router)
router.include_router(businesses.router)
router.include_router(approvals.router)
router.include_router(metrics.router)
router.include_router(webhooks.router)
router.include_router(vectors.router)
router.include_router(learning.router)
router.include_router(ollama.router)
router.include_router(api_keys.router)
router.include_router(settings.router)
