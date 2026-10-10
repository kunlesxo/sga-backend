import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

TELEGRAM_API_BASE = "https://api.telegram.org"
REQUEST_TIMEOUT = 15.0


def _url(method: str) -> str:
    return f"{TELEGRAM_API_BASE}/bot{settings.TELEGRAM_BOT_TOKEN}/{method}"


async def _call(method: str, payload: dict) -> Optional[dict]:
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not configured")
        return None

    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.post(_url(method), json=payload)
    except httpx.HTTPError as exc:
        logger.error("Telegram %s network error: %s", method, exc)
        return None

    try:
        body = response.json()
    except ValueError:
        logger.error("Telegram %s returned non-JSON: %s", method, response.text[:200])
        return None

    if not body.get("ok"):
        logger.warning("Telegram %s failed: %s", method, body.get("description"))
        return None

    return body.get("result")


async def send_message(chat_id: int, text: str, reply_markup: Optional[dict] = None) -> Optional[dict]:
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    return await _call("sendMessage", payload)


async def create_invite_link(chat_id: int, member_limit: int = 1) -> Optional[str]:
    """
    Create a single-use, short-lived invite link for a chat.
    Returns the invite URL or None on failure.
    """
    expire_date = int(
        (datetime.now(timezone.utc) + timedelta(hours=settings.INVITE_LINK_EXPIRE_HOURS)).timestamp()
    )
    result = await _call(
        "createChatInviteLink",
        {
            "chat_id": chat_id,
            "member_limit": member_limit,
            "expire_date": expire_date,
        },
    )
    if not result:
        return None
    return result.get("invite_link")


async def revoke_invite_link(chat_id: int, invite_link: str) -> bool:
    result = await _call(
        "revokeChatInviteLink",
        {"chat_id": chat_id, "invite_link": invite_link},
    )
    return result is not None


async def ban_chat_member(chat_id: int, user_id: int) -> bool:
    result = await _call(
        "banChatMember",
        {"chat_id": chat_id, "user_id": user_id, "revoke_messages": False},
    )
    return result is not None


async def unban_chat_member(chat_id: int, user_id: int) -> bool:
    result = await _call(
        "unbanChatMember",
        {"chat_id": chat_id, "user_id": user_id, "only_if_banned": True},
    )
    return result is not None


async def set_webhook(url: str, secret_token: str) -> bool:
    result = await _call(
        "setWebhook",
        {
            "url": url,
            "secret_token": secret_token,
            "allowed_updates": ["message"],
        },
    )
    return result is not None
