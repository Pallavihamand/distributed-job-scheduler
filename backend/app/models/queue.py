from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey
)
from sqlalchemy.sql import func
from app.database import Base


class Queue(Base):
    __tablename__ = "queues"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    project_id = Column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    retry_policy_id = Column(
        Integer,
        ForeignKey("retry_policies.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    name = Column(
        String(100),
        nullable=False
    )

    priority = Column(
        Integer,
        default=0,
        nullable=False,
        index=True
    )

    concurrency_limit = Column(
        Integer,
        default=5,
        nullable=False
    )

    is_paused = Column(
        Boolean,
        default=False,
        nullable=False,
        index=True
    )

    created_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )