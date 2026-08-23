from sqlalchemy import (
    Column,
    Integer,
    DateTime,
    ForeignKey,
)
from sqlalchemy.sql import func

from app.database import Base


class WorkerHeartbeat(Base):
    __tablename__ = "worker_heartbeats"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    worker_id = Column(
        Integer,
        ForeignKey("workers.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    active_jobs = Column(
        Integer,
        nullable=False,
        default=0
    )

    created_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False,
        index=True
    )