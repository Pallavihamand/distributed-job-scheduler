from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.organization import Organization
from app.schemas.organization import (
    OrganizationCreate,
    OrganizationResponse,
)
from app.security import get_current_user


router = APIRouter(
    prefix="/organizations",
    tags=["Organizations"],
)


# ============================================================
# CREATE ORGANIZATION
# ============================================================

@router.post(
    "",
    response_model=OrganizationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_organization(
    data: OrganizationCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):

    organization = Organization(
        name=data.name,
        owner_id=current_user.id,
    )

    db.add(organization)
    db.commit()
    db.refresh(organization)

    return organization


# ============================================================
# GET ALL ORGANIZATIONS
# ============================================================

@router.get(
    "",
    response_model=list[OrganizationResponse],
)
def get_organizations(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):

    return (
        db.query(Organization)
        .filter(
            Organization.owner_id == current_user.id
        )
        .order_by(Organization.id.asc())
        .all()
    )


# ============================================================
# GET ORGANIZATION
# ============================================================

@router.get(
    "/{organization_id}",
    response_model=OrganizationResponse,
)
def get_organization(
    organization_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):

    organization = (
        db.query(Organization)
        .filter(
            Organization.id == organization_id,
            Organization.owner_id == current_user.id,
        )
        .first()
    )

    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    return organization
