from fastapi import APIRouter

from app.api.v1 import businesses, approvals, metrics, webhooks, vectors, learning, billing, api_keys

router = APIRouter()

router.include_router(businesses.router)
router.include_router(approvals.router)
router.include_router(metrics.router)
router.include_router(webhooks.router)
router.include_router(vectors.router)
router.include_router(learning.router)
router.include_router(billing.router)
router.include_router(api_keys.router)