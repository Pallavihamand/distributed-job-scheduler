from pydantic import BaseModel, Field


class QueueCreate(BaseModel):
    project_id: int
    name: str

    priority: int = Field(
        default=1,
        ge=1,
        le=10,
    )

    concurrency_limit: int = Field(
        default=5,
        ge=1,
        le=100,
    )


class QueueResponse(BaseModel):
    id: int
    project_id: int
    name: str
    priority: int
    concurrency_limit: int
    is_paused: bool

    class Config:
        from_attributes = True