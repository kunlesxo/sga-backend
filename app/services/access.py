import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.student import Student
from app.services import telegram

logger = logging.getLogger(__name__)


def expiry_from_now() -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=settings.ACCESS_DURATION_DAYS)


def is_expired(student: Student) -> bool:
    return datetime.now(timezone.utc) >= student.access_expiry


async def revoke_student(student: Student, db: AsyncSession) -> bool:
    """
    Remove the student from both chats, then mark them revoked.
    Ban then unban — this removes them from the group without a permanent block,
    so a future re-purchase can rejoin cleanly.
    """
    classroom_ok = await telegram.ban_chat_member(
        settings.TELEGRAM_CLASSROOM_CHAT_ID, student.telegram_id
    )
    discussion_ok = await telegram.ban_chat_member(
        settings.TELEGRAM_DISCUSSION_CHAT_ID, student.telegram_id
    )

    await telegram.unban_chat_member(
        settings.TELEGRAM_CLASSROOM_CHAT_ID, student.telegram_id
    )
    await telegram.unban_chat_member(
        settings.TELEGRAM_DISCUSSION_CHAT_ID, student.telegram_id
    )

    student.revoked = True
    student.revoked_at = datetime.now(timezone.utc)
    await db.commit()

    logger.info(
        "Revoked student tg=%s (classroom=%s discussion=%s)",
        student.telegram_id,
        classroom_ok,
        discussion_ok,
    )
    return classroom_ok and discussion_ok


async def find_expired_students(db: AsyncSession, limit: int = 500) -> list[Student]:
    stmt = (
        select(Student)
        .where(Student.revoked.is_(False))
        .where(Student.access_expiry < datetime.now(timezone.utc))
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())
