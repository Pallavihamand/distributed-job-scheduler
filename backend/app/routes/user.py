
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse
from app.security import hash_password


router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


# ============================================================
# CREATE USER
# ============================================================

@router.post(
    "",
    response_model=UserResponse,
    status_code=201,
)
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
):
    """
    Create a new user.

    Password is securely hashed before storing
    it in the database.
    """

    # --------------------------------------------------------
    # CHECK EMAIL
    # --------------------------------------------------------

    existing_user = (
        db.query(User)
        .filter(User.email == user_data.email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered",
        )

    # --------------------------------------------------------
    # HASH PASSWORD
    # --------------------------------------------------------

    hashed_password = hash_password(
        user_data.password
    )

    # --------------------------------------------------------
    # CREATE USER
    # --------------------------------------------------------

    user = User(
        full_name=user_data.name,
        email=user_data.email,
        password_hash=hashed_password,
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user

