import json
import logging

from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.transaction import Transaction
from app.models.webhook_event import WebhookEvent
from app.services import paystack

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhook", tags=["paystack"])


@router.post("/paystack")
async def paystack_webhook(
    request: Request,
    x_paystack_signature: str = Header(default="", alias="x-paystack-signature"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    raw_body = await request.body()

    if not paystack.verify_webhook_signature(raw_body, x_paystack_signature):
        logger.warning("Rejected Paystack webhook: bad signature")
        return {"status": "rejected"}

    try:
        body = json.loads(raw_body)
    except json.JSONDecodeError:
        logger.warning("Rejected Paystack webhook: bad JSON")
        return {"status": "rejected"}

    event_type = body.get("event", "unknown")

    # Log the event
    event = WebhookEvent(
        source="paystack",
        event_type=event_type,
        payload=body,
        processed=False,
    )
    db.add(event)

    if event_type != "charge.success":
        event.processed = True
        await db.commit()
        return {"status": "ignored"}

    data = body.get("data", {})
    reference = data.get("reference")
    if not reference:
        event.processed = True
        await db.commit()
        return {"status": "ignored"}

    # Idempotent — skip if we already have it
    existing = await db.scalar(
        select(Transaction).where(Transaction.reference == reference)
    )
    if existing:
        event.processed = True
        await db.commit()
        return {"status": "duplicate"}

    amount = int(data.get("amount", 0))
    currency = data.get("currency", "NGN")
    status = data.get("status", "unknown")

    if status != "success" or currency != "NGN" or not paystack.is_valid_amount(amount):
        event.processed = True
        await db.commit()
        logger.warning(
            "Skipping webhook reference=%s status=%s currency=%s amount=%s",
            reference, status, currency, amount,
        )
        return {"status": "invalid"}

    customer = data.get("customer") or {}
    tx = Transaction(
        reference=reference,
        paystack_id=data.get("id"),
        amount_kobo=amount,
        currency=currency,
        status=status,
        customer_email=customer.get("email"),
        customer_name=(
            f"{(customer.get('first_name') or '').strip()} "
            f"{(customer.get('last_name') or '').strip()}"
        ).strip() or None,
        paid_at=data.get("paid_at"),
        raw_response=data,
    )
    db.add(tx)
    event.processed = True
    await db.commit()

    logger.info("Stored transaction from webhook: %s", reference)
    return {"status": "ok"}
