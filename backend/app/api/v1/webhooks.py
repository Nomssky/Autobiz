from typing import Any, Dict

from fastapi import APIRouter

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/{webhook_type}", summary="Generic webhook endpoint")
async def generic_webhook(webhook_type: str, payload: Dict[str, Any]):
    return {"status": "received", "webhook_type": webhook_type}
