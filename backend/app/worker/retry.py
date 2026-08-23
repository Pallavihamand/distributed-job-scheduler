
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models.job import Job
from app.models.dead_letter import DeadLetterJob


def calculate_retry_delay(
    attempt: int,
    strategy: str = "exponential",
    base_delay: int = 5,
) -> int:
    """
    Calculate retry delay in seconds.

    Supported:
    - fixed
    - linear
    - exponential
    """

    strategy = strategy.lower()

    if strategy == "fixed":
        return base_delay

    if strategy == "linear":
        return base_delay * attempt

    # Default: exponential
    return base_delay * (2 ** max(attempt - 1, 0))


def handle_job_failure(
    db: Session,
    job: Job,
    error_message: str,
    retry_strategy: str = "exponential",
    base_delay: int = 5,
):
    """
    Retry a failed job or move it to the Dead Letter Queue.
    """

    job.error_message = error_message
    job.failed_at = datetime.utcnow()

    # Increase attempt count
    job.attempts += 1

    # ---------------------------------------------------------
    # RETRY
    # ---------------------------------------------------------

    if job.attempts < job.max_attempts:

        delay = calculate_retry_delay(
            attempt=job.attempts,
            strategy=retry_strategy,
            base_delay=base_delay,
        )

        job.status = "QUEUED"

        job.next_retry_at = (
            datetime.utcnow()
            + timedelta(seconds=delay)
        )

        job.worker_id = None
        job.claimed_at = None
        job.started_at = None

        db.commit()
        db.refresh(job)

        return {
            "action": "RETRY",
            "attempt": job.attempts,
            "delay_seconds": delay,
        }

    # ---------------------------------------------------------
    # DEAD LETTER QUEUE
    # ---------------------------------------------------------

    job.status = "DEAD_LETTER"

    job.worker_id = None

    dead_job = DeadLetterJob(
        job_id=job.id,
        reason="Maximum retry attempts exceeded",
        last_error=error_message,
        attempts=job.attempts,
    )

    db.add(dead_job)
    db.commit()

    return {
        "action": "DLQ",
        "attempts": job.attempts,
    }