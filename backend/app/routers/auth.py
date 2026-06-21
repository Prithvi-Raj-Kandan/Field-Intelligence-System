from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.services.auth import authenticate_user, create_access_token, create_user, get_user_by_email

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_auth_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=settings.auth_cookie_name,
        value=token,
        httponly=True,
        secure=settings.cookie_secure or settings.is_production,
        samesite="lax",
        max_age=settings.jwt_expire_minutes * 60,
        path="/",
    )


def _clear_auth_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.auth_cookie_name,
        path="/",
        httponly=True,
        secure=settings.cookie_secure or settings.is_production,
        samesite="lax",
    )


@router.post("/login", response_model=TokenResponse)
def login(
    body: LoginRequest,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
) -> TokenResponse:
    user = authenticate_user(db, body.email, body.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = create_access_token(user_id=user.id, role=user.role)
    _set_auth_cookie(response, token)
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(
    body: RegisterRequest,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
) -> TokenResponse:
    if body.role == "manager" and not settings.allow_manager_registration:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Manager registration is disabled. Contact an administrator.",
        )

    if get_user_by_email(db, body.email) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user = create_user(
        db,
        email=body.email,
        password=body.password,
        role=body.role,
        name=body.name,
    )
    token = create_access_token(user_id=user.id, role=user.role)
    _set_auth_cookie(response, token)
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response) -> None:
    _clear_auth_cookie(response)


@router.get("/me", response_model=UserResponse)
def read_me(current_user: Annotated[User, Depends(get_current_user)]) -> UserResponse:
    return UserResponse.model_validate(current_user)
