
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.worker import Worker


router = APIRouter(
    prefix="/workers",
    tags=["Workers"],
)


# ============================================================
# REGISTER / START WORKER
# ============================================================

@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
)
def register_worker(
    name: str,
    hostname: str | None = None,
    concurrency_limit: int = 5,
    db: Session = Depends(get_db),
):
    """
    Register a worker or bring an existing worker online.
    """

    if not name.strip():
        raise HTTPException(
            status_code=400,
            detail="Worker name cannot be empty",
        )

    if concurrency_limit < 1:
        raise HTTPException(
            status_code=400,
            detail="Concurrency limit must be at least 1",
        )

    if concurrency_limit > 100:
        raise HTTPException(
            status_code=400,
            detail="Concurrency limit cannot exceed 100",
        )

    existing_worker = (
        db.query(Worker)
        .filter(Worker.name == name)
        .first()
    )

    now = datetime.utcnow()

    if existing_worker:
        existing_worker.status = "ONLINE"
        existing_worker.hostname = hostname
        existing_worker.concurrency_limit = concurrency_limit
        existing_worker.last_heartbeat = now
        existing_worker.is_active = True

        if existing_worker.started_at is None:
            existing_worker.started_at = now

        db.commit()
        db.refresh(existing_worker)

        return existing_worker

    worker = Worker(
        name=name,
        hostname=hostname,
        status="ONLINE",
        active_jobs=0,
        concurrency_limit=concurrency_limit,
        is_active=True,
        started_at=now,
        last_heartbeat=now,
    )

    db.add(worker)
    db.commit()
    db.refresh(worker)

    return worker


# ============================================================
# WORKER HEARTBEAT
# ============================================================

@router.post("/{worker_id}/heartbeat")
def worker_heartbeat(
    worker_id: int,
    db: Session = Depends(get_db),
):
    """
    Update worker heartbeat and mark worker online.
    """

    worker = (
        db.query(Worker)
        .filter(Worker.id == worker_id)
        .first()
    )

    if not worker:
        raise HTTPException(
            status_code=404,
            detail="Worker not found",
        )

    if not worker.is_active:
        raise HTTPException(
            status_code=400,
            detail="Worker is inactive",
        )

    worker.last_heartbeat = datetime.utcnow()
    worker.status = "ONLINE"

    db.commit()
    db.refresh(worker)

    return {
        "worker_id": worker.id,
        "status": worker.status,
        "last_heartbeat": worker.last_heartbeat,
    }


# ============================================================
# WORKER STATUS
# ============================================================

@router.get("/{worker_id}/status")
def get_worker_status(
    worker_id: int,
    db: Session = Depends(get_db),
):
    """
    Return the current worker status and capacity.
    """

    worker = (
        db.query(Worker)
        .filter(Worker.id == worker_id)
        .first()
    )

    if not worker:
        raise HTTPException(
            status_code=404,
            detail="Worker not found",
        )

    available_slots = max(
        worker.concurrency_limit - worker.active_jobs,
        0,
    )

    return {
        "worker_id": worker.id,
        "name": worker.name,
        "status": worker.status,
        "is_active": worker.is_active,
        "active_jobs": worker.active_jobs,
        "concurrency_limit": worker.concurrency_limit,
        "available_slots": available_slots,
        "last_heartbeat": worker.last_heartbeat,
    }


# ============================================================
# MARK STALE WORKERS OFFLINE
# ============================================================

@router.post("/health-check")
def worker_health_check(
    timeout_seconds: int = 60,
    db: Session = Depends(get_db),
):
    """
    Mark active workers OFFLINE when their heartbeat
    has not been received within the timeout period.
    """

    if timeout_seconds < 10:
        raise HTTPException(
            status_code=400,
            detail="Timeout must be at least 10 seconds",
        )

    cutoff_time = (
        datetime.utcnow()
        - timedelta(seconds=timeout_seconds)
    )

    stale_workers = (
        db.query(Worker)
        .filter(
            Worker.is_active == True,
            Worker.last_heartbeat.isnot(None),
            Worker.last_heartbeat < cutoff_time,
        )
        .all()
    )

    for worker in stale_workers:
        worker.status = "OFFLINE"

    db.commit()

    return {
        "message": "Worker health check completed",
        "offline_count": len(stale_workers),
        "workers": [
            {
                "worker_id": worker.id,
                "name": worker.name,
                "status": worker.status,
            }
            for worker in stale_workers
        ],
    }


# ============================================================
# DEACTIVATE WORKER
# ============================================================

@router.post("/{worker_id}/deactivate")
def deactivate_worker(
    worker_id: int,
    db: Session = Depends(get_db),
):
    """
    Deactivate a worker.
    """

    worker = (
        db.query(Worker)
        .filter(Worker.id == worker_id)
        .first()
    )

    if not worker:
        raise HTTPException(
            status_code=404,
            detail="Worker not found",
        )

    if worker.active_jobs > 0:
        raise HTTPException(
            status_code=400,
            detail=(
                "Cannot deactivate worker while it "
                "has active jobs"
            ),
        )

    worker.is_active = False
    worker.status = "OFFLINE"

    db.commit()
    db.refresh(worker)

    return {
        "message": "Worker deactivated successfully",
        "worker_id": worker.id,
        "status": worker.status,
        "is_active": worker.is_active,
    }


# ============================================================
# GET ALL WORKERS
# ============================================================

@router.get("")
def get_workers(
    db: Session = Depends(get_db),
):
    """
    Get all registered workers.
    """

    return (
        db.query(Worker)
        .order_by(Worker.id.asc())
        .all()
    )


# ============================================================
# GET SINGLE WORKER
# ============================================================

@router.get("/{worker_id}")
def get_worker(
    worker_id: int,
    db: Session = Depends(get_db),
):
    """
    Get a worker by ID.
    """

    worker = (
        db.query(Worker)
        .filter(Worker.id == worker_id)
        .first()
    )

    if not worker:
        raise HTTPException(
            status_code=404,
            detail="Worker not found",
        )

    return worker

