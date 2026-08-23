from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Boolean,
    JSON,
)
from sqlalchemy.sql import func

from app.database import Base


class ScheduledJob(Base):
    __tablename__ = "scheduled_jobs"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    queue_id = Column(
        Integer,
        ForeignKey(
            "queues.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    job_type = Column(
        String(100),
        nullable=False,
    )

    payload = Column(
        JSON,
        nullable=False,
    )

    priority = Column(
        Integer,
        default=0,
        nullable=False,
    )

    max_attempts = Column(
        Integer,
        default=3,
        nullable=False,
    )

    cron_expression = Column(
        String(100),
        nullable=False,
    )

    next_run_at = Column(
        DateTime,
        nullable=False,
        index=True,
    )

    last_run_at = Column(
        DateTime,
        nullable=True,
    )

    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
    )

    created_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )