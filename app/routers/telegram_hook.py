import logging

from fastapi import APIRouter, Request

from app.bot.handlers import handle_update
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhook", tags=["telegram"])


@router.post("/telegram")
async def telegram_webhook(request: Request) -> dict:
    # Verify Telegram secret token header if configured
    secret = request.headers.get("x-telegram-bot-api-secret-token", "")
    if settings.TELEGRAM_WEBHOOK_SECRET and secret != settings.TELEGRAM_WEBHOOK_SECRET:
        logger.warning("Rejected Telegram webhook: bad secret")
        return {"ok": False}

    try:
        update = await request.json()
    except Exception:
        return {"ok": False}

    try:
        await handle_update(update)
    except Exception as exc:
        logger.exception("Telegram handler error: %s", exc)

    return {"ok": True}
