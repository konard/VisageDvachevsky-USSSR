"""
Authentication service
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserLogin, TokenResponse
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_token_type,
)
from app.core.exceptions import (
    UserAlreadyExistsError,
    InvalidCredentialsError,
    UserNotFoundError,
)


class AuthService:
    """Service for authentication operations"""

    def __init__(self, db: Optional[AsyncSession]):
        self.db = db

    async def register(self, user_data: UserCreate) -> User:
        """Register a new user"""
        # Check if user already exists
        existing_user = await self._get_user_by_email(user_data.email)
        if existing_user:
            raise UserAlreadyExistsError(user_data.email)

        # Create new user
        user = User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=get_password_hash(user_data.password),
            role=UserRole.USER,
            is_active=True,
        )

        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def login(self, credentials: UserLogin) -> TokenResponse:
        """Login user and return tokens"""
        # Get user by email
        user = await self._get_user_by_email(credentials.email)
        if not user:
            raise InvalidCredentialsError()

        # Verify password
        if not verify_password(credentials.password, user.hashed_password):
            raise InvalidCredentialsError()

        # Check if user is active
        if not user.is_active:
            raise InvalidCredentialsError()

        # Generate tokens
        access_token = create_access_token({"sub": str(user.id), "role": user.role.value})
        refresh_token = create_refresh_token({"sub": str(user.id)})

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
        )

    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        """Refresh access token"""
        # Decode and verify refresh token
        payload = decode_token(refresh_token)
        verify_token_type(payload, "refresh")

        user_id = payload.get("sub")
        if not user_id:
            raise InvalidCredentialsError()

        # Get user from database
        if self.db:
            user = await self._get_user_by_id(user_id)
            if not user or not user.is_active:
                raise InvalidCredentialsError()
            role = user.role.value
        else:
            # If DB not available, use role from token (for stateless refresh)
            role = payload.get("role", UserRole.USER.value)

        # Generate new tokens
        access_token = create_access_token({"sub": user_id, "role": role})
        new_refresh_token = create_refresh_token({"sub": user_id})

        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
        )

    async def _get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        if not self.db:
            return None

        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def _get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        if not self.db:
            return None

        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
