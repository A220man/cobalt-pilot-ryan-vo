# Authentication dependencies and utilities
from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token, TokenData
from app.core.database import get_db
from app.core.oidc import validate_id_token, get_user_info
from app.models.plugin import User

security = HTTPBearer(auto_error=False)


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """Get current user from JWT token (optional - returns None if not authenticated)."""
    if not credentials:
        return None

    token_data = decode_token(credentials.credentials)
    if not token_data:
        return None

    # Fetch user from database
    user = await db.get(User, token_data.sub)
    return user


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Get current user from JWT token (required - raises 401 if not authenticated)."""
    user = await get_current_user_optional(credentials, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get current active user (required - raises 403 if inactive)."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return current_user


def require_role(required_role: str):
    """Dependency factory for role-based access control."""
    async def role_checker(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        if required_role not in current_user.roles and "admin" not in current_user.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{required_role}' required",
            )
        return current_user
    return role_checker


# Role dependencies
require_viewer = require_role("viewer")
require_operator = require_role("operator")
require_admin = require_role("admin")


class OIDCStateData:
    """Simple in-memory state storage for PKCE (use Redis in production)."""
    _states: dict[str, dict] = {}

    @classmethod
    def store(cls, state: str, data: dict):
        cls._states[state] = data

    @classmethod
    def retrieve_and_delete(cls, state: str) -> Optional[dict]:
        return cls._states.pop(state, None)
