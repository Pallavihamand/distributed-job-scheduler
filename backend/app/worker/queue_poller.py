from datetime import datetime

from sqlalchemy.orm import Session

from app.models.job import Job
from app.models.queue import Queue


def claim_next_job(
    db: Session,
    worker_id: int,
):
    """
    Claim the highest-priority available job
    from an active, non-paused queue.

    Returns the claimed Job or None.
    """

    now = datetime.utcnow()

    # Find a queue that is NOT paused
    queue = (
        db.query(Queue)
        .filter(
            Queue.is_paused == False,
        )
        .order_by(
            Queue.priority.desc(),
            Queue.id.asc(),
        )
        .first()
    )

    if not queue:
        return None

    # Check queue concurrency
    active_jobs = (
        db.query(Job)
        .filter(
            Job.queue_id == queue.id,
            Job.status.in_(["CLAIMED", "RUNNING"]),
        )
        .count()
    )

    if active_jobs >= queue.concurrency_limit:
        return None

    # Find highest-priority available job
    job = (
        db.query(Job)
        .filter(
            Job.queue_id == queue.id,
            Job.status == "QUEUED",
        )
        .filter(
            (Job.scheduled_at.is_(None))
            | (Job.scheduled_at <= now)
        )
        .filter(
            (Job.next_retry_at.is_(None))
            | (Job.next_retry_at <= now)
        )
        .order_by(
            Job.priority.desc(),
            Job.created_at.asc(),
        )
        .with_for_update(skip_locked=True)
        .first()
    )

    if not job:
        return None

    # Claim job
    job.status = "CLAIMED"
    job.worker_id = worker_id
    job.claimed_at = now

    db.commit()
    db.refresh(job)

    return job