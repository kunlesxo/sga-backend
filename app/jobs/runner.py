"""Standalone scheduler process — run with: python -m app.jobs.runner"""
import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.jobs.revoke_expired import run as revoke_run

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-5s [%(name)s] %(message)s",
)
logger = logging.getLogger("sga.jobs")


async def main() -> None:
    scheduler = AsyncIOScheduler(timezone="Africa/Lagos")
    scheduler.add_job(
        revoke_run,
        trigger=CronTrigger(hour=2, minute=0),
        id="revoke_expired",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler started. Expiry job runs daily at 02:00 WAT.")

    # Run once on startup to catch missed runs while sleeping
    try:
        await revoke_run()
    except Exception as exc:
        logger.exception("Startup revoke run failed: %s", exc)

    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
