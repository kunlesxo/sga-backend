import logging

from app.database import AsyncSessionLocal
from app.services.access import find_expired_students, revoke_student

logger = logging.getLogger(__name__)


async def run() -> int:
    """Find expired students and revoke their Telegram access. Returns count revoked."""
    revoked_count = 0
    async with AsyncSessionLocal() as db:
        students = await find_expired_students(db, limit=500)
        for student in students:
            try:
                await revoke_student(student, db)
                revoked_count += 1
            except Exception as exc:
                logger.exception(
                    "Failed to revoke student tg=%s: %s", student.telegram_id, exc
                )
    if revoked_count:
        logger.info("Revoked %d expired students", revoked_count)
    return revoked_count
