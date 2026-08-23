from pydantic import BaseModel


class ProjectCreate(BaseModel):
    organization_id: int
    name: str
    description: str | None = None


class ProjectResponse(BaseModel):
    id: int
    organization_id: int
    name: str
    description: str | None

    class Config:
        from_attributes = True