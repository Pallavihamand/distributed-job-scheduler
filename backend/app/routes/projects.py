from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.organization import Organization
from app.models.project import Project
from app.schemas.project import (
    ProjectCreate,
    ProjectResponse,
)
from app.security import get_current_user


router = APIRouter(
    prefix="/projects",
    tags=["Projects"],
)


# ============================================================
# GET ALL PROJECTS
# ============================================================

@router.get(
    "",
    response_model=list[ProjectResponse],
)
def get_projects(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):

    return (
        db.query(Project)
        .join(
            Organization,
            Project.organization_id == Organization.id,
        )
        .filter(
            Organization.owner_id == current_user.id
        )
        .order_by(Project.id.asc())
        .all()
    )


# ============================================================
# CREATE PROJECT
# ============================================================

@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_project(
    data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):

    # --------------------------------------------------------
    # CHECK ORGANIZATION BELONGS TO CURRENT USER
    # --------------------------------------------------------

    organization = (
        db.query(Organization)
        .filter(
            Organization.id == data.organization_id,
            Organization.owner_id == current_user.id,
        )
        .first()
    )

    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    # --------------------------------------------------------
    # CREATE PROJECT
    # --------------------------------------------------------

    project = Project(
        organization_id=data.organization_id,
        name=data.name,
        description=data.description,
    )

    db.add(project)
    db.commit()
    db.refresh(project)

    return project


# ============================================================
# GET SINGLE PROJECT
# ============================================================

@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):

    project = (
        db.query(Project)
        .join(
            Organization,
            Project.organization_id == Organization.id,
        )
        .filter(
            Project.id == project_id,
            Organization.owner_id == current_user.id,
        )
        .first()
    )

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    return project

