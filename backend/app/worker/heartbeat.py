from datetime import datetime

from sqlalchemy.orm import Session

from app.models.worker import Worker
from app.models.worker_heartbeat import WorkerHeartbeat


def send_heartbeat(
    db: Session,
    worker_id: int,
):
    """
    Update worker heartbeat and store heartbeat history.
    """

    worker = (
        db.query(Worker)
        .filter(Worker.id == worker_id)
        .first()
    )

    if not worker:
        return False

    now = datetime.utcnow()

    worker.status = "ONLINE"
    worker.last_heartbeat = now
    worker.is_active = True

    heartbeat = WorkerHeartbeat(
        worker_id=worker_id,
        active_jobs=worker.active_jobs,
    )

    db.add(heartbeat)
    db.commit()

    return True