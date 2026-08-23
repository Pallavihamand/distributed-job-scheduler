
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.job import Job
from app.models.queue import Queue
from app.schemas.job import JobCreate, JobResponse


router = APIRouter(
    prefix="/jobs",
    tags=["Jobs"],
)


# ============================================================
# CREATE SINGLE JOB
# ============================================================

@router.post(
    "",
    response_model=JobResponse,
    status_code=201,
)
def create_job(
    job_data: JobCreate,
    db: Session = Depends(get_db),
):
    """
    Create an immediate or scheduled job.
    """

    queue = (
        db.query(Queue)
        .filter(Queue.id == job_data.queue_id)
        .first()
    )

    if not queue:
        raise HTTPException(
            status_code=404,
            detail="Queue not found",
        )

    # Do not allow new jobs into a paused queue
    if queue.is_paused:
        raise HTTPException(
            status_code=400,
            detail="Queue is paused. Resume the queue before creating jobs.",
        )

    job_status = (
        "SCHEDULED"
        if job_data.scheduled_at
        else "QUEUED"
    )

    job = Job(
        queue_id=job_data.queue_id,
        job_type=job_data.job_type,
        payload=job_data.payload,
        priority=job_data.priority,
        max_attempts=job_data.max_attempts,
        attempts=0,
        scheduled_at=job_data.scheduled_at,
        status=job_status,
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    return job


# ============================================================
# GET ALL JOBS
# ============================================================

@router.get(
    "",
    response_model=list[JobResponse],
)
def get_jobs(
    skip: int = 0,
    limit: int = 50,
    status: str | None = None,
    queue_id: int | None = None,
    db: Session = Depends(get_db),
):
    """
    Get jobs with pagination and filtering.
    """

    if skip < 0:
        skip = 0

    if limit < 1:
        limit = 1

    if limit > 100:
        limit = 100

    query = db.query(Job)

    if status:
        query = query.filter(
            Job.status == status
        )

    if queue_id is not None:
        query = query.filter(
            Job.queue_id == queue_id
        )

    return (
        query
        .order_by(
            Job.priority.desc(),
            Job.created_at.asc(),
        )
        .offset(skip)
        .limit(limit)
        .all()
    )


# ============================================================
# CREATE BATCH JOBS
# ============================================================

@router.post(
    "/batch",
    response_model=list[JobResponse],
    status_code=201,
)
def create_batch_jobs(
    jobs_data: list[JobCreate],
    db: Session = Depends(get_db),
):
    """
    Create multiple jobs in one database transaction.

    Maximum: 100 jobs per batch.
    """

    if not jobs_data:
        raise HTTPException(
            status_code=400,
            detail="Batch cannot be empty",
        )

    if len(jobs_data) > 100:
        raise HTTPException(
            status_code=400,
            detail="Maximum 100 jobs allowed per batch",
        )

    # --------------------------------------------------------
    # Validate all queues before creating any jobs
    # --------------------------------------------------------

    queue_ids = {
        job_data.queue_id
        for job_data in jobs_data
    }

    queues = (
        db.query(Queue)
        .filter(Queue.id.in_(queue_ids))
        .all()
    )

    existing_queue_ids = {
        queue.id
        for queue in queues
    }

    missing_queue_ids = (
        queue_ids - existing_queue_ids
    )

    if missing_queue_ids:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Queue(s) not found: "
                f"{sorted(missing_queue_ids)}"
            ),
        )

    # --------------------------------------------------------
    # Do not create jobs in paused queues
    # --------------------------------------------------------

    paused_queue_ids = {
        queue.id
        for queue in queues
        if queue.is_paused
    }

    if paused_queue_ids:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Queue(s) are paused: "
                f"{sorted(paused_queue_ids)}"
            ),
        )

    # --------------------------------------------------------
    # Create jobs
    # --------------------------------------------------------

    jobs = []

    for job_data in jobs_data:

        job_status = (
            "SCHEDULED"
            if job_data.scheduled_at
            else "QUEUED"
        )

        job = Job(
            queue_id=job_data.queue_id,
            job_type=job_data.job_type,
            payload=job_data.payload,
            priority=job_data.priority,
            max_attempts=job_data.max_attempts,
            attempts=0,
            scheduled_at=job_data.scheduled_at,
            status=job_status,
        )

        jobs.append(job)

    db.add_all(jobs)
    db.commit()

    for job in jobs:
        db.refresh(job)

    return jobs


# ============================================================
# GET SINGLE JOB
# ============================================================

@router.get(
    "/{job_id}",
    response_model=JobResponse,
)
def get_job(
    job_id: int,
    db: Session = Depends(get_db),
):
    """
    Get a single job by ID.
    """

    job = (
        db.query(Job)
        .filter(Job.id == job_id)
        .first()
    )

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found",
        )

    return job


# ============================================================
# RETRY FAILED / DEAD JOB
# ============================================================

@router.post(
    "/{job_id}/retry",
    response_model=JobResponse,
)
def retry_job(
    job_id: int,
    db: Session = Depends(get_db),
):
    """
    Manually retry a failed or dead-letter job.
    """

    job = (
        db.query(Job)
        .filter(Job.id == job_id)
        .first()
    )

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found",
        )

    if job.status not in [
        "FAILED",
        "DEAD",
        "DEAD_LETTER",
    ]:
        raise HTTPException(
            status_code=400,
            detail=(
                "Only failed or dead-letter jobs "
                "can be retried"
            ),
        )

    # Check queue state
    queue = (
        db.query(Queue)
        .filter(Queue.id == job.queue_id)
        .first()
    )

    if queue and queue.is_paused:
        raise HTTPException(
            status_code=400,
            detail="Cannot retry while queue is paused",
        )

    # Reset execution state
    job.status = "QUEUED"

    job.worker_id = None
    job.claimed_at = None
    job.started_at = None
    job.completed_at = None
    job.failed_at = None
    job.next_retry_at = None
    job.error_message = None

    # Start a fresh manual retry cycle
    job.attempts = 0

    db.commit()
    db.refresh(job)

    return job


# ============================================================
# DELETE JOB
# ============================================================

@router.delete(
    "/{job_id}",
)
def delete_job(
    job_id: int,
    db: Session = Depends(get_db),
):
    """
    Delete a job that is not currently executing.
    """

    job = (
        db.query(Job)
        .filter(Job.id == job_id)
        .first()
    )

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found",
        )

    if job.status in [
        "CLAIMED",
        "RUNNING",
    ]:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete an active job",
        )

    db.delete(job)
    db.commit()

    return {
        "message": "Job deleted successfully",
        "job_id": job_id,
    }


