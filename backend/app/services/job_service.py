from datetime import datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.job import Job
from app.models.queue import Queue
from app.models.job_execution import JobExecution


# ============================================================
# CLAIM NEXT JOB
# ============================================================

def claim_next_job(
    db: Session,
    worker_id: int,
):
    """
    Atomically claim the next available job.

    Supports:
        - Immediate jobs
        - Scheduled jobs
        - Delayed jobs
        - Retry jobs
        - Paused queues
        - Queue concurrency limits
        - Priority
        - Multiple workers

    Lifecycle:

        QUEUED/SCHEDULED
              ↓
           CLAIMED
              ↓
           RUNNING
              ↓
          COMPLETED

    Uses MySQL/InnoDB row locking with SKIP LOCKED.
    """

    now = datetime.utcnow()

    # --------------------------------------------------------
    # Count active jobs per queue
    # --------------------------------------------------------

    active_jobs = (
        db.query(
            Job.queue_id.label("queue_id"),
            func.count(Job.id).label("active_count"),
        )
        .filter(
            Job.status.in_(["CLAIMED", "RUNNING"])
        )
        .group_by(Job.queue_id)
        .subquery()
    )

    # --------------------------------------------------------
    # Find next eligible job
    # --------------------------------------------------------

    job = (
        db.query(Job)
        .join(
            Queue,
            Job.queue_id == Queue.id,
        )
        .outerjoin(
            active_jobs,
            Job.queue_id == active_jobs.c.queue_id,
        )
        .filter(

            # Immediate and scheduled jobs
            Job.status.in_(["QUEUED", "SCHEDULED"]),

            # Job must not already be assigned
            Job.worker_id.is_(None),

            # Queue must not be paused
            Queue.is_paused.is_(False),

            # Scheduled/delayed job must be due
            (
                Job.scheduled_at.is_(None)
                |
                (Job.scheduled_at <= now)
            ),

            # Retry delay must be finished
            (
                Job.next_retry_at.is_(None)
                |
                (Job.next_retry_at <= now)
            ),

            # Respect queue concurrency
            (
                active_jobs.c.active_count.is_(None)
                |
                (
                    active_jobs.c.active_count
                    < Queue.concurrency_limit
                )
            ),
        )
        .order_by(
            Job.priority.desc(),
            Job.created_at.asc(),
        )
        .with_for_update(
            skip_locked=True
        )
        .first()
    )

    # No available job
    if job is None:
        return None

    # --------------------------------------------------------
    # CLAIM JOB
    # --------------------------------------------------------

    job.status = "CLAIMED"
    job.worker_id = worker_id
    job.claimed_at = now
    job.updated_at = now

    db.commit()
    db.refresh(job)

    return job


# ============================================================
# START JOB EXECUTION
# ============================================================

def start_job_execution(
    db: Session,
    job: Job,
    worker_id: int,
):
    """
    Move:

        CLAIMED → RUNNING

    Create JobExecution record.
    """

    now = datetime.utcnow()

    job.status = "RUNNING"
    job.started_at = now

    # Increment attempt
    job.attempts += 1

    execution = JobExecution(
        job_id=job.id,
        worker_id=worker_id,
        attempt_number=job.attempts,
        status="RUNNING",
        started_at=now,
    )

    db.add(execution)

    db.commit()
    db.refresh(execution)

    return execution


# ============================================================
# COMPLETE JOB
# ============================================================

def complete_job(
    db: Session,
    job: Job,
    execution: JobExecution,
):
    """
    Move:

        RUNNING → COMPLETED
    """

    now = datetime.utcnow()

    execution.status = "COMPLETED"
    execution.finished_at = now

    if execution.started_at:
        execution.duration_ms = int(
            (
                now - execution.started_at
            ).total_seconds() * 1000
        )

    job.status = "COMPLETED"
    job.completed_at = now
    job.updated_at = now

    db.commit()
    db.refresh(job)

    return job


# ============================================================
# CALCULATE RETRY DELAY
# ============================================================

def calculate_retry_delay(
    attempt_number: int,
    strategy: str = "exponential",
    base_delay: int = 5,
):
    """
    Retry strategies:

        fixed:
            5, 5, 5

        linear:
            5, 10, 15

        exponential:
            5, 10, 20
    """

    if strategy == "fixed":
        return base_delay

    if strategy == "linear":
        return base_delay * attempt_number

    # exponential
    return base_delay * (
        2 ** (attempt_number - 1)
    )


# ============================================================
# FAIL JOB
# ============================================================

def fail_job(
    db: Session,
    job: Job,
    execution: JobExecution,
    error_message: str,
):
    """
    Handle failed execution.

    If attempts remain:

        RUNNING
           ↓
        FAILED
           ↓
        QUEUED
           ↓
        retry

    Otherwise:

        RUNNING
           ↓
        FAILED
           ↓
          DEAD
    """

    now = datetime.utcnow()

    # --------------------------------------------------------
    # Finish execution record
    # --------------------------------------------------------

    execution.status = "FAILED"
    execution.finished_at = now
    execution.error_message = error_message

    if execution.started_at:
        execution.duration_ms = int(
            (
                now - execution.started_at
            ).total_seconds() * 1000
        )

    # --------------------------------------------------------
    # Update job failure information
    # --------------------------------------------------------

    job.error_message = error_message
    job.failed_at = now
    job.updated_at = now

    # --------------------------------------------------------
    # RETRY AVAILABLE
    # --------------------------------------------------------

    if job.attempts < job.max_attempts:

        delay = calculate_retry_delay(
            attempt_number=job.attempts,
            strategy="exponential",
            base_delay=5,
        )

        job.status = "QUEUED"

        job.next_retry_at = (
            now + timedelta(seconds=delay)
        )

        # Release worker
        job.worker_id = None
        job.claimed_at = None
        job.started_at = None

        db.commit()
        db.refresh(job)

        return {
            "status": "RETRY",
            "job": job,
            "retry_delay": delay,
        }

    # --------------------------------------------------------
    # DEAD LETTER
    # --------------------------------------------------------

    job.status = "DEAD"

    job.worker_id = None
    job.claimed_at = None

    db.commit()
    db.refresh(job)

    return {
        "status": "DEAD",
        "job": job,
        "retry_delay": None,
    }