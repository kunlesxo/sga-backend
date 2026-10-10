import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.transaction import Transaction
from app.services import paystack

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["verify"])


@router.get("/verify/{reference}")
async def verify(reference: str, db: AsyncSession = Depends(get_db)) -> dict:
    """
    Check a Paystack reference. Called by the success page.
    Never grants access — just tells the frontend whether to show the Telegram button.
    """
    reference = reference.strip()
    if not reference:
        raise HTTPException(status_code=400, detail="Reference is required")

    # Fast path: already stored
    existing = await db.scalar(
        select(Transaction).where(Transaction.reference == reference)
    )
    if existing and existing.status == "success":
        return {
            "verified": True,
            "reference": reference,
            "message": "Payment confirmed",
        }

    # Slow path: verify with Paystack
    tx = await paystack.verify_transaction(reference)
    if tx is None:
        return {
            "verified": False,
            "reference": reference,
            "message": "We could not verify this payment yet.",
        }

    if tx.status != "success":
        return {
            "verified": False,
            "reference": reference,
            "message": f"Payment status is '{tx.status}'.",
        }

    if tx.currency != "NGN":
        return {
            "verified": False,
            "reference": reference,
            "message": "Payment currency is not NGN.",
        }

    if not paystack.is_valid_amount(tx.amount):
        return {
            "verified": False,
            "reference": reference,
            "message": "Payment amount does not match the course price.",
        }

    # Store it
    record = Transaction(
        reference=tx.reference,
        paystack_id=tx.id,
        amount_kobo=tx.amount,
        currency=tx.currency,
        status=tx.status,
        customer_email=(tx.customer.email if tx.customer else None),
        customer_name=(
            f"{(tx.customer.first_name or '').strip()} {(tx.customer.last_name or '').strip()}".strip()
            if tx.customer
            else None
        ),
        paid_at=tx.paid_at,
        raw_response=tx.model_dump(),
    )
    db.add(record)
    await db.commit()

    return {
        "verified": True,
        "reference": reference,
        "message": "Payment confirmed",
    }
