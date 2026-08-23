from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class JobCreate(BaseModel):
    queue_id: int
    job_type: str = Field(..., min_length=1, max_length=100)

    payload: dict[str, Any] = Field(
        default_factory=dict
    )

    priority: int = 0

    max_attempts: int = Field(
        default=3,
        ge=1,
        le=20
    )

    scheduled_at: Optional[datetime] = None


class JobResponse(BaseModel):
    id: int
    queue_id: int
    job_type: str
    payload: dict[str, Any]

    status: str

    priority: int

    attempts: int
    max_attempts: int

    scheduled_at: Optional[datetime] = None
    next_retry_at: Optional[datetime] = None

    worker_id: Optional[int] = None

    claimed_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None

    error_message: Optional[str] = None

    created_at: datetime

    class Config:
        from_attributes = True