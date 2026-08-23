from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.database import Base


class RetryPolicy(Base):
    __tablename__ = "retry_policies"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    name = Column(
        String(100),
        nullable=False
    )

    strategy = Column(
        String(30),
        nullable=False
    )

    max_attempts = Column(
        Integer,
        default=3,
        nullable=False
    )

    base_delay_seconds = Column(
        Integer,
        default=5,
        nullable=False
    )

    created_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )