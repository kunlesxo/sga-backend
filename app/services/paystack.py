import hashlib
import hmac
import logging
from typing import Any, Optional

import httpx

from app.config import settings
from app.schemas.paystack import PaystackTransaction

logger = logging.getLogger(__name__)

PAYSTACK_API_BASE = "https://api.paystack.co"
VERIFY_TIMEOUT = 15.0


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json",
    }


async def verify_transaction(reference: str) -> Optional[PaystackTransaction]:
    """
    Call Paystack /transaction/verify/{reference}.
    Returns a PaystackTransaction on success, or None on any failure.
    """
    url = f"{PAYSTACK_API_BASE}/transaction/verify/{reference}"
    try:
        async with httpx.AsyncClient(timeout=VERIFY_TIMEOUT) as client:
            response = await client.get(url, headers=_headers())
    except httpx.HTTPError as exc:
        logger.error("Paystack verify network error for %s: %s", reference, exc)
        return None

    if response.status_code != 200:
        logger.warning(
            "Paystack verify non-200 for %s: %s %s",
            reference,
            response.status_code,
            response.text[:200],
        )
        return None

    try:
        body = response.json()
    except ValueError:
        logger.error("Paystack verify returned non-JSON for %s", reference)
        return None

    if not body.get("status"):
        logger.warning("Paystack verify status=false for %s: %s", reference, body.get("message"))
        return None

    data = body.get("data")
    if not data:
        return None

    try:
        return PaystackTransaction(**data)
    except Exception as exc:
        logger.error("Failed to parse Paystack transaction for %s: %s", reference, exc)
        return None


def is_valid_amount(amount_kobo: int) -> bool:
    return settings.PAYSTACK_MIN_AMOUNT_KOBO <= amount_kobo <= settings.PAYSTACK_MAX_AMOUNT_KOBO


def verify_webhook_signature(raw_body: bytes, signature: str) -> bool:
    """
    Validate Paystack webhook HMAC-SHA512 signature.
    Returns True only when the signature matches the payload.
    """
    if not signature:
        return False
    if not settings.PAYSTACK_SECRET_KEY:
        logger.error("PAYSTACK_SECRET_KEY not configured; cannot verify webhook")
        return False

    expected = hmac.new(
        settings.PAYSTACK_SECRET_KEY.encode("utf-8"),
        raw_body,
        hashlib.sha512,
    ).hexdigest()

    return hmac.compare_digest(expected, signature)


def transaction_to_dict(tx: PaystackTransaction) -> dict[str, Any]:
    return tx.model_dump()
