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


class DeadLetterJob(Base):
    __tablename__ = "dead_letter_jobs"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    job_id = Column(
        Integer,
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )

    reason = Column(
        Text,
        nullable=False
    )

    last_error = Column(
        Text,
        nullable=True
    )

    attempts = Column(
        Integer,
        nullable=False
    )

    moved_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )