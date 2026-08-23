
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.project import Project
from app.models.queue import Queue
from app.models.job import Job
from app.schemas.queue import QueueCreate, QueueResponse


router = APIRouter(
    prefix="/queues",
    tags=["Queues"],
)


# ============================================================
# GET ALL QUEUES
# ============================================================

@router.get(
    "",
    response_model=list[QueueResponse],
)
def get_queues(
    db: Session = Depends(get_db),
):
    """
    Return all queues.

    Used by the frontend dashboard and queue management page.
    """

    queues = (
        db.query(Queue)
        .order_by(Queue.id.desc())
        .all()
    )

    return queues


# ============================================================
# CREATE QUEUE
# ============================================================

@router.post(
    "",
    response_model=QueueResponse,
)
def create_queue(
    data: QueueCreate,
    db: Session = Depends(get_db),
):
    project = (
        db.query(Project)
        .filter(Project.id == data.project_id)
        .first()
    )

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    queue = Queue(
        project_id=data.project_id,
        name=data.name,
        priority=data.priority,
        concurrency_limit=data.concurrency_limit,
    )

    db.add(queue)
    db.commit()
    db.refresh(queue)

    return queue


# ============================================================
# PAUSE QUEUE
# ============================================================

@router.post("/{queue_id}/pause")
def pause_queue(
    queue_id: int,
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

    queue.is_paused = True

    db.commit()
    db.refresh(queue)

    return {
        "message": "Queue paused",
        "queue_id": queue.id,
        "is_paused": queue.is_paused,
    }


# ============================================================
# RESUME QUEUE
# ============================================================

@router.post("/{queue_id}/resume")
def resume_queue(
    queue_id: int,
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

    queue.is_paused = False

    db.commit()
    db.refresh(queue)

    return {
        "message": "Queue resumed",
        "queue_id": queue.id,
        "is_paused": queue.is_paused,
    }


# ============================================================
# QUEUE STATISTICS
# ============================================================

@router.get("/{queue_id}/stats")
def queue_stats(
    queue_id: int,
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

    total = (
        db.query(func.count(Job.id))
        .filter(Job.queue_id == queue_id)
        .scalar()
    )

    queued = (
        db.query(func.count(Job.id))
        .filter(
            Job.queue_id == queue_id,
            Job.status == "QUEUED",
        )
        .scalar()
    )

    running = (
        db.query(func.count(Job.id))
        .filter(
            Job.queue_id == queue_id,
            Job.status == "RUNNING",
        )
        .scalar()
    )

    completed = (
        db.query(func.count(Job.id))
        .filter(
            Job.queue_id == queue_id,
            Job.status == "COMPLETED",
        )
        .scalar()
    )

    failed = (
        db.query(func.count(Job.id))
        .filter(
            Job.queue_id == queue_id,
            Job.status == "FAILED",
        )
        .scalar()
    )

    dead = (
        db.query(func.count(Job.id))
        .filter(
            Job.queue_id == queue_id,
            Job.status == "DEAD",
        )
        .scalar()
    )

    return {
        "queue_id": queue.id,
        "queue_name": queue.name,
        "is_paused": queue.is_paused,
        "priority": queue.priority,
        "concurrency_limit": queue.concurrency_limit,
        "total_jobs": total,
        "queued_jobs": queued,
        "running_jobs": running,
        "completed_jobs": completed,
        "failed_jobs": failed,
        "dead_jobs": dead,
    }

