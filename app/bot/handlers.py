import logging
from datetime import datetime, timezone

from sqlalchemy import select

from app.bot import messages
from app.config import settings
from app.database import AsyncSessionLocal
from app.models.student import Student
from app.models.transaction import Transaction
from app.services import paystack, telegram
from app.services.access import expiry_from_now

logger = logging.getLogger(__name__)


async def handle_update(update: dict) -> None:
    message = update.get("message")
    if not message:
        return

    text = (message.get("text") or "").strip()
    chat = message.get("chat") or {}
    chat_id = chat.get("id")
    from_user = message.get("from") or {}
    user_id = from_user.get("id")

    if not chat_id or not user_id:
        return

    if text.startswith("/start"):
        parts = text.split(maxsplit=1)
        reference = parts[1].strip() if len(parts) > 1 else ""
        if not reference:
            await telegram.send_message(chat_id, messages.NO_REFERENCE)
            return
        await handle_start(chat_id, user_id, from_user, reference)
        return

    if text in ("/help", "/support"):
        await telegram.send_message(
            chat_id, messages.HELP.format(support=settings.SUPPORT_WHATSAPP)
        )
        return


async def handle_start(chat_id: int, user_id: int, from_user: dict, reference: str) -> None:
    async with AsyncSessionLocal() as db:
        # Look up any student already linked to this reference
        existing = await db.scalar(
            select(Student).join(Transaction).where(Transaction.reference == reference)
        )

        if existing:
            if existing.telegram_id == user_id:
                # Same user — return the same links (idempotent)
                await _send_welcome(chat_id, existing)
                return
            # Reference already used by a different Telegram account
            await telegram.send_message(
                chat_id,
                messages.ALREADY_LINKED.format(support=settings.SUPPORT_WHATSAPP),
            )
            return

        # No existing student — check if we have the transaction
        tx = await db.scalar(
            select(Transaction).where(Transaction.reference == reference)
        )

        # If not in DB, verify directly with Paystack
        if tx is None:
            remote = await paystack.verify_transaction(reference)
            if remote is None:
                await telegram.send_message(
                    chat_id,
                    messages.VERIFY_FAILED.format(support=settings.SUPPORT_WHATSAPP),
                )
                return
            if (
                remote.status != "success"
                or remote.currency != "NGN"
                or not paystack.is_valid_amount(remote.amount)
            ):
                await telegram.send_message(
                    chat_id,
                    messages.VERIFY_FAILED.format(support=settings.SUPPORT_WHATSAPP),
                )
                return
            tx = Transaction(
                reference=remote.reference,
                paystack_id=remote.id,
                amount_kobo=remote.amount,
                currency=remote.currency,
                status=remote.status,
                customer_email=(remote.customer.email if remote.customer else None),
                customer_name=(
                    f"{(remote.customer.first_name or '').strip()} "
                    f"{(remote.customer.last_name or '').strip()}"
                ).strip() or None,
                paid_at=remote.paid_at,
                raw_response=remote.model_dump(),
            )
            db.add(tx)
            await db.flush()

        if tx.status != "success" or not paystack.is_valid_amount(tx.amount_kobo):
            await telegram.send_message(
                chat_id,
                messages.VERIFY_FAILED.format(support=settings.SUPPORT_WHATSAPP),
            )
            return

        # Generate two single-use invite links
        classroom_link = await telegram.create_invite_link(
            settings.TELEGRAM_CLASSROOM_CHAT_ID
        )
        discussion_link = await telegram.create_invite_link(
            settings.TELEGRAM_DISCUSSION_CHAT_ID
        )

        if not classroom_link or not discussion_link:
            logger.error(
                "Failed to create invite links for tg=%s ref=%s",
                user_id, reference,
            )
            await telegram.send_message(chat_id, messages.ERROR_SENDING_LINKS)
            return

        now = datetime.now(timezone.utc)
        student = Student(
            telegram_id=user_id,
            telegram_username=from_user.get("username"),
            telegram_first_name=from_user.get("first_name"),
            telegram_last_name=from_user.get("last_name"),
            transaction_id=tx.id,
            access_start=now,
            access_expiry=expiry_from_now(),
            classroom_invite_link=classroom_link,
            discussion_invite_link=discussion_link,
        )
        db.add(student)
        await db.commit()
        await db.refresh(student)

        logger.info("New student tg=%s ref=%s", user_id, reference)
        await _send_welcome(chat_id, student)


async def _send_welcome(chat_id: int, student: Student) -> None:
    expiry_str = student.access_expiry.strftime("%d %b %Y")
    text = messages.WELCOME_TEMPLATE.format(expiry=expiry_str)

    # Inline keyboard with both invite links
    keyboard = {
        "inline_keyboard": [
            [{"text": "JOIN CLASSROOM", "url": student.classroom_invite_link}],
            [{"text": "JOIN DISCUSSION & Q&A", "url": student.discussion_invite_link}],
        ]
    }
    await telegram.send_message(chat_id, text, reply_markup=keyboard)
