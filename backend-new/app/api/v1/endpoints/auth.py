"""
Authentication API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas.user import (
    UserCreate,
    UserResponse,
    UserLogin,
    TokenResponse,
    TokenRefresh,
)
from app.services.auth_service import AuthService
from app.core.exceptions import UserAlreadyExistsError, InvalidCredentialsError

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Register a new user
    """
    service = AuthService(db)
    try:
        user = await service.register(user_data)
        return user
    except UserAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db),
):
    """
    Login user and get access token
    """
    service = AuthService(db)
    try:
        tokens = await service.login(credentials)
        return tokens
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    token_data: TokenRefresh,
):
    """
    Refresh access token using refresh token
    """
    service = AuthService(None)  # No DB needed for token refresh
    try:
        tokens = await service.refresh_token(token_data.refresh_token)
        return tokens
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    # current_user: User = Depends(get_current_user),  # TODO: Add when auth is ready
):
    """
    Logout user (invalidate token on client side)
    """
    # Token invalidation happens on client side
    # Future: Implement token blacklist in Redis
    return None


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    # current_user: User = Depends(get_current_user),  # TODO: Add when auth is ready
    db: AsyncSession = Depends(get_db),
):
    """
    Get current authenticated user
    """
    # TODO: Implement after authentication middleware is ready
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Authentication not yet implemented",
    )
