from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    JSON,
    Index,
)
from sqlalchemy.sql import func

from app.database import Base


class Job(Base):
    __tablename__ = "jobs"

    # ========================================================
    # PRIMARY KEY
    # ========================================================

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # ========================================================
    # QUEUE
    # ========================================================

    queue_id = Column(
        Integer,
        ForeignKey(
            "queues.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    # ========================================================
    # JOB TYPE
    # ========================================================

    job_type = Column(
        String(100),
        nullable=False,
        index=True
    )

    # ========================================================
    # JOB PAYLOAD
    # ========================================================

    payload = Column(
        JSON,
        nullable=False
    )

    # ========================================================
    # STATUS
    #
    # Possible values:
    #
    # QUEUED
    # SCHEDULED
    # CLAIMED
    # RUNNING
    # COMPLETED
    # FAILED
    # DEAD_LETTER
    # CANCELLED
    # ========================================================

    status = Column(
        String(30),
        nullable=False,
        default="QUEUED",
        index=True
    )

    # ========================================================
    # PRIORITY
    # ========================================================

    priority = Column(
        Integer,
        nullable=False,
        default=0,
        index=True
    )

    # ========================================================
    # RETRY CONFIGURATION
    # ========================================================

    max_attempts = Column(
        Integer,
        nullable=False,
        default=3
    )

    attempts = Column(
        Integer,
        nullable=False,
        default=0
    )

    # ========================================================
    # SCHEDULING
    # ========================================================

    scheduled_at = Column(
        DateTime,
        nullable=True,
        index=True
    )

    next_retry_at = Column(
        DateTime,
        nullable=True,
        index=True
    )

    # ========================================================
    # WORKER
    # ========================================================

    worker_id = Column(
        Integer,
        ForeignKey(
            "workers.id",
            ondelete="SET NULL"
        ),
        nullable=True,
        index=True
    )

    # ========================================================
    # EXECUTION TIMESTAMPS
    # ========================================================

    claimed_at = Column(
        DateTime,
        nullable=True
    )

    started_at = Column(
        DateTime,
        nullable=True
    )

    completed_at = Column(
        DateTime,
        nullable=True
    )

    failed_at = Column(
        DateTime,
        nullable=True
    )

    # ========================================================
    # ERROR
    # ========================================================

    error_message = Column(
        Text,
        nullable=True
    )

    # ========================================================
    # TIMESTAMPS
    # ========================================================

    created_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False,
        index=True
    )

    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )


# ============================================================
# WORKER POLLING INDEX
# ============================================================

Index(
    "idx_jobs_worker_poll",
    Job.queue_id,
    Job.status,
    Job.priority,
    Job.created_at
)


# ============================================================
# RETRY / SCHEDULING INDEX
# ============================================================

Index(
    "idx_jobs_retry_schedule",
    Job.status,
    Job.next_retry_at,
    Job.scheduled_at
)