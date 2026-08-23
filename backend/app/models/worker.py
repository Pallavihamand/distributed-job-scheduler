from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
)
from sqlalchemy.sql import func

from app.database import Base


class Worker(Base):
    __tablename__ = "workers"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    name = Column(
        String(100),
        nullable=False,
        unique=True
    )

    status = Column(
        String(30),
        nullable=False,
        default="OFFLINE",
        index=True
    )

    hostname = Column(
        String(255),
        nullable=True
    )

    active_jobs = Column(
        Integer,
        nullable=False,
        default=0
    )

    concurrency_limit = Column(
        Integer,
        nullable=False,
        default=5
    )

    is_active = Column(
        Boolean,
        default=True,
        nullable=False
    )

    started_at = Column(
        DateTime,
        nullable=True
    )

    last_heartbeat = Column(
        DateTime,
        nullable=True,
        index=True
    )

    created_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )