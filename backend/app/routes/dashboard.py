
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.job import Job
from app.models.queue import Queue
from app.models.worker import Worker


router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)


# ============================================================
# DASHBOARD
# ============================================================

@router.get("")
def get_dashboard(
    db: Session = Depends(get_db),
):
    """
    Return all data required by the frontend dashboard.
    """

    # --------------------------------------------------------
    # JOB STATISTICS
    # --------------------------------------------------------

    total_jobs = (
        db.query(func.count(Job.id))
        .scalar()
        or 0
    )

    running_jobs = (
        db.query(func.count(Job.id))
        .filter(
            Job.status.in_(["CLAIMED", "RUNNING"])
        )
        .scalar()
        or 0
    )

    completed_jobs = (
        db.query(func.count(Job.id))
        .filter(
            Job.status == "COMPLETED"
        )
        .scalar()
        or 0
    )

    failed_jobs = (
        db.query(func.count(Job.id))
        .filter(
            Job.status.in_(["FAILED", "DEAD_LETTER"])
        )
        .scalar()
        or 0
    )

    # --------------------------------------------------------
    # RECENT JOBS
    # --------------------------------------------------------

    recent_job_rows = (
        db.query(Job, Queue.name)
        .join(
            Queue,
            Queue.id == Job.queue_id
        )
        .order_by(
            Job.created_at.desc()
        )
        .limit(5)
        .all()
    )

    recent_jobs = []

    for job, queue_name in recent_job_rows:

        duration = None

        if job.started_at and job.completed_at:
            duration_seconds = (
                job.completed_at - job.started_at
            ).total_seconds()

            duration = f"{duration_seconds:.1f}s"

        elif job.started_at and job.status in [
            "RUNNING",
            "CLAIMED",
        ]:
            duration_seconds = (
                datetime.utcnow() - job.started_at
            ).total_seconds()

            duration = f"{duration_seconds:.1f}s"

        elif job.status in [
            "QUEUED",
            "SCHEDULED",
        ]:
            duration = "-"

        else:
            duration = "-"

        recent_jobs.append(
            {
                "id": job.id,
                "job_type": job.job_type,
                "queue": queue_name,
                "status": job.status,
                "duration": duration,
                "priority": job.priority,
                "created_at": job.created_at,
            }
        )

    # --------------------------------------------------------
    # WORKERS
    # --------------------------------------------------------

    workers_db = (
        db.query(Worker)
        .order_by(Worker.id.asc())
        .all()
    )

    workers = []

    for worker in workers_db:
        workers.append(
            {
                "id": worker.id,
                "name": worker.name,
                "active_jobs": worker.active_jobs,
                "concurrency_limit": worker.concurrency_limit,
                "status": worker.status,
                "is_active": worker.is_active,
                "last_heartbeat": worker.last_heartbeat,
            }
        )

    # --------------------------------------------------------
    # QUEUES
    # --------------------------------------------------------

    queues_db = (
        db.query(Queue)
        .order_by(Queue.id.asc())
        .all()
    )

    queues = []

    for queue in queues_db:

        running = (
            db.query(func.count(Job.id))
            .filter(
                Job.queue_id == queue.id,
                Job.status.in_(
                    ["CLAIMED", "RUNNING"]
                ),
            )
            .scalar()
            or 0
        )

        pending = (
            db.query(func.count(Job.id))
            .filter(
                Job.queue_id == queue.id,
                Job.status.in_(
                    ["QUEUED", "SCHEDULED"]
                ),
            )
            .scalar()
            or 0
        )

        queues.append(
            {
                "id": queue.id,
                "name": queue.name,
                "running": running,
                "pending": pending,
                "concurrency": queue.concurrency_limit,
                "priority": queue.priority,
                "is_paused": queue.is_paused,
                "status": (
                    "Paused"
                    if queue.is_paused
                    else "Active"
                ),
            }
        )

    # --------------------------------------------------------
    # FINAL RESPONSE
    # --------------------------------------------------------

    return {
        "statistics": {
            "total_jobs": total_jobs,
            "running_jobs": running_jobs,
            "completed_jobs": completed_jobs,
            "failed_jobs": failed_jobs,
        },
        "recent_jobs": recent_jobs,
        "workers": workers,
        "queues": queues,
    }

