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


class JobLog(Base):
    __tablename__ = "job_logs"

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

    execution_id = Column(
        Integer,
        ForeignKey("job_executions.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )

    level = Column(
        String(20),
        nullable=False,
        default="INFO"
    )

    message = Column(
        Text,
        nullable=False
    )

    created_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False,
        index=True
    )