
import time
import threading
from datetime import datetime

from croniter import croniter

from app.database import SessionLocal
from app.models.scheduled_job import ScheduledJob
from app.models.job import Job


_scheduler_thread = None
_scheduler_running = False


def process_scheduled_jobs():
    """
    Find all active recurring jobs whose next_run_at
    has arrived and create executable Job records.
    """

    db = SessionLocal()

    try:
        now = datetime.utcnow()

        scheduled_jobs = (
            db.query(ScheduledJob)
            .filter(
                ScheduledJob.is_active == True,
                ScheduledJob.next_run_at <= now,
            )
            .all()
        )

        created_count = 0

        for scheduled_job in scheduled_jobs:

            job = Job(
                queue_id=scheduled_job.queue_id,
                job_type=scheduled_job.job_type,
                payload=scheduled_job.payload,
                priority=scheduled_job.priority,
                max_attempts=scheduled_job.max_attempts,
                attempts=0,
                status="QUEUED",
                scheduled_at=None,
            )

            db.add(job)

            # Calculate next execution time
            cron = croniter(
                scheduled_job.cron_expression,
                scheduled_job.next_run_at,
            )

            scheduled_job.next_run_at = cron.get_next(
                datetime
            )

            created_count += 1

        db.commit()

        return created_count

    except Exception as exc:
        db.rollback()
        print(
            f"Scheduler error: {exc}"
        )
        return 0

    finally:
        db.close()


def scheduler_loop():
    """
    Background scheduler loop.

    Checks for due recurring jobs every 5 seconds.
    """

    global _scheduler_running

    print("Scheduler started")

    while _scheduler_running:

        try:
            created = process_scheduled_jobs()

            if created:
                print(
                    f"Scheduler created {created} job(s)"
                )

        except Exception as exc:
            print(
                f"Scheduler loop error: {exc}"
            )

        time.sleep(5)

    print("Scheduler stopped")


def start_scheduler():
    """
    Start scheduler in a background thread.
    """

    global _scheduler_thread
    global _scheduler_running

    if _scheduler_running:
        return

    _scheduler_running = True

    _scheduler_thread = threading.Thread(
        target=scheduler_loop,
        daemon=True,
    )

    _scheduler_thread.start()


def stop_scheduler():
    """
    Stop scheduler background thread.
    """

    global _scheduler_running
    global _scheduler_thread

    _scheduler_running = False

    if _scheduler_thread:
        _scheduler_thread.join(
            timeout=2
        )

    _scheduler_thread = None

