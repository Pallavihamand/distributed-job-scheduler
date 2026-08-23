from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Text,
)
from sqlalchemy.sql import func

from app.database import Base


class JobExecution(Base):
    __tablename__ = "job_executions"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    job_id = Column(
        Integer,
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    worker_id = Column(
        Integer,
        ForeignKey("workers.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    attempt_number = Column(
        Integer,
        nullable=False,
        default=1
    )

    status = Column(
        String(30),
        nullable=False,
        index=True
    )

    started_at = Column(
        DateTime,
        nullable=True
    )

    finished_at = Column(
        DateTime,
        nullable=True
    )

    duration_ms = Column(
        Integer,
        nullable=True
    )

    error_message = Column(
        Text,
        nullable=True
    )

    created_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )