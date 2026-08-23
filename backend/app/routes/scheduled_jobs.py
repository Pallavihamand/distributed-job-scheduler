
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from croniter import croniter

from app.database import get_db
from app.models.scheduled_job import ScheduledJob
from app.models.queue import Queue
from app.models.job import Job


router = APIRouter(
    prefix="/scheduled-jobs",
    tags=["Scheduled Jobs"],
)


# ============================================================
# CREATE RECURRING JOB
# ============================================================

@router.post("")
def create_recurring_job(
    queue_id: int,
    job_type: str,
    payload: dict,
    cron_expression: str,
    next_run_at: datetime,
    priority: int = 0,
    max_attempts: int = 3,
    db: Session = Depends(get_db),
):
    queue = (
        db.query(Queue)
        .filter(Queue.id == queue_id)
        .first()
    )

    if not queue:
        raise HTTPException(
            status_code=404,
            detail="Queue not found",
        )

    # Validate cron expression
    try:
        croniter(
            cron_expression,
            next_run_at,
        )
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Invalid cron expression",
        )

    scheduled_job = ScheduledJob(
        queue_id=queue_id,
        job_type=job_type,
        payload=payload,
        cron_expression=cron_expression,
        next_run_at=next_run_at,
        priority=priority,
        max_attempts=max_attempts,
        is_active=True,
    )

    db.add(scheduled_job)
    db.commit()
    db.refresh(scheduled_job)

    return scheduled_job


# ============================================================
# GET RECURRING JOBS
# ============================================================

@router.get("")
def get_recurring_jobs(
    db: Session = Depends(get_db),
):
    return (
        db.query(ScheduledJob)
        .order_by(
            ScheduledJob.next_run_at.asc()
        )
        .all()
    )


# ============================================================
# RUN DUE RECURRING JOBS
# ============================================================

@router.post("/process")
def process_recurring_jobs(
    db: Session = Depends(get_db),
):
    """
    Find recurring jobs whose next_run_at has arrived,
    create normal jobs, and calculate the next execution time.
    """

    now = datetime.utcnow()

    scheduled_jobs = (
        db.query(ScheduledJob)
        .filter(
            ScheduledJob.is_active == True,
            ScheduledJob.next_run_at <= now,
        )
        .all()
    )

    created_jobs = []

    for scheduled_job in scheduled_jobs:

        # Create normal executable Job
        job = Job(
            queue_id=scheduled_job.queue_id,
            job_type=scheduled_job.job_type,
            payload=scheduled_job.payload,
            priority=scheduled_job.priority,
            max_attempts=scheduled_job.max_attempts,
            attempts=0,
            scheduled_at=None,
            status="QUEUED",
        )

        db.add(job)

        # Calculate next cron execution
        cron = croniter(
            scheduled_job.cron_expression,
            scheduled_job.next_run_at,
        )

        scheduled_job.next_run_at = cron.get_next(datetime)

        created_jobs.append(job)

    db.commit()

    for job in created_jobs:
        db.refresh(job)

    return {
        "message": "Recurring jobs processed",
        "created_count": len(created_jobs),
        "jobs": [
            {
                "id": job.id,
                "queue_id": job.queue_id,
                "job_type": job.job_type,
                "status": job.status,
            }
            for job in created_jobs
        ],
    }


# ============================================================
# PAUSE RECURRING JOB
# ============================================================

@router.post("/{scheduled_job_id}/pause")
def pause_recurring_job(
    scheduled_job_id: int,
    db: Session = Depends(get_db),
):
    scheduled_job = (
        db.query(ScheduledJob)
        .filter(
            ScheduledJob.id == scheduled_job_id
        )
        .first()
    )

    if not scheduled_job:
        raise HTTPException(
            status_code=404,
            detail="Scheduled job not found",
        )

    scheduled_job.is_active = False

    db.commit()

    return {
        "message": "Recurring job paused",
        "scheduled_job_id": scheduled_job.id,
        "is_active": False,
    }


# ============================================================
# RESUME RECURRING JOB
# ============================================================

@router.post("/{scheduled_job_id}/resume")
def resume_recurring_job(
    scheduled_job_id: int,
    db: Session = Depends(get_db),
):
    scheduled_job = (
        db.query(ScheduledJob)
        .filter(
            ScheduledJob.id == scheduled_job_id
        )
        .first()
    )

    if not scheduled_job:
        raise HTTPException(
            status_code=404,
            detail="Scheduled job not found",
        )

    scheduled_job.is_active = True

    db.commit()

    return {
        "message": "Recurring job resumed",
        "scheduled_job_id": scheduled_job.id,
        "is_active": True,
    }


# ============================================================
# DELETE RECURRING JOB
# ============================================================

@router.delete("/{scheduled_job_id}")
def delete_recurring_job(
    scheduled_job_id: int,
    db: Session = Depends(get_db),
):
    scheduled_job = (
        db.query(ScheduledJob)
        .filter(
            ScheduledJob.id == scheduled_job_id
        )
        .first()
    )

    if not scheduled_job:
        raise HTTPException(
            status_code=404,
            detail="Scheduled job not found",
        )

    db.delete(scheduled_job)
    db.commit()

    return {
        "message": "Recurring job deleted",
        "scheduled_job_id": scheduled_job_id,
    }

