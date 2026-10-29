# Authentication API routes
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import secrets

from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import create_access_token, generate_pkce_pair
from app.core.auth import (
    get_current_user,
    get_current_active_user,
    require_viewer,
    require_operator,
    require_admin,
    OIDCStateData,
)
from app.core.oidc import (
    build_authorization_url,
    build_logout_url,
    exchange_code_for_tokens,
    get_user_info,
    validate_id_token,
)
from app.models.plugin import User

router = APIRouter(prefix="/auth", tags=["authentication"])
settings = get_settings()


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: Optional[str] = None


class AuthURLResponse(BaseModel):
    auth_url: str
    state: str
    code_verifier: str
    nonce: str


class CallbackRequest(BaseModel):
    code: str
    state: str
    code_verifier: str
    nonce: str


@router.get("/login", response_model=AuthURLResponse)
async def login(redirect_uri: str = Query(...)):
    """Initiate OIDC login flow with PKCE."""
    state = secrets.token_urlsafe(32)
    nonce = secrets.token_urlsafe(32)
    code_verifier, code_challenge = generate_pkce_pair()

    # Store PKCE state
    OIDCStateData.store(state, {
        "code_verifier": code_verifier,
        "nonce": nonce,
        "redirect_uri": redirect_uri,
    })

    auth_url = build_authorization_url(
        redirect_uri=redirect_uri,
        state=state,
        nonce=nonce,
        code_challenge=code_challenge,
    )

    return AuthURLResponse(
        auth_url=auth_url,
        state=state,
        code_verifier=code_verifier,
        nonce=nonce,
    )


@router.post("/callback", response_model=TokenResponse)
async def callback(
    request: CallbackRequest,
    db: AsyncSession = Depends(get_db),
):
    """Handle OIDC callback and exchange code for tokens."""
    # Retrieve stored state
    stored = OIDCStateData.retrieve_and_delete(request.state)
    if not stored:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired state",
        )

    if stored["code_verifier"] != request.code_verifier:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Code verifier mismatch",
        )

    if stored["nonce"] != request.nonce:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nonce mismatch",
        )

    redirect_uri = stored["redirect_uri"]

    # Exchange code for tokens
    tokens = await exchange_code_for_tokens(
        code=request.code,
        redirect_uri=redirect_uri,
        code_verifier=request.code_verifier,
    )
    if not tokens:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to exchange code for tokens",
        )

    # Validate ID token
    id_token_payload = await validate_id_token(tokens.id_token, request.nonce)
    if not id_token_payload:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ID token",
        )

    # Get user info
    user_info = await get_user_info(tokens.access_token)
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to fetch user info",
        )

    # Upsert user in database
    user = await db.get(User, user_info.sub)
    if not user:
        user = User(
            id=user_info.sub,
            email=user_info.email,
            username=user_info.preferred_username,
            full_name=user_info.name,
            roles=user_info.roles,
            is_active=True,
        )
        db.add(user)
    else:
        user.email = user_info.email
        user.username = user_info.preferred_username
        user.full_name = user_info.name
        user.roles = user_info.roles
        user.last_login_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(user)

    # Create access token for our API
    access_token = create_access_token({
        "sub": user.id,
        "email": user.email,
        "roles": user.roles,
    })

    return TokenResponse(
        access_token=access_token,
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post("/logout")
async def logout(redirect_uri: str = Query(...)):
    """Logout and redirect to Keycloak logout."""
    logout_url = build_logout_url(redirect_uri)
    return {"logout_url": logout_url}


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_active_user)):
    """Get current user info."""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "username": current_user.username,
        "full_name": current_user.full_name,
        "roles": current_user.roles,
        "is_active": current_user.is_active,
        "is_superuser": current_user.is_superuser,
        "created_at": current_user.created_at,
        "last_login_at": current_user.last_login_at,
    }


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(current_user: User = Depends(get_current_active_user)):
    """Refresh access token."""
    access_token = create_access_token({
        "sub": current_user.id,
        "email": current_user.email,
        "roles": current_user.roles,
    })
    return TokenResponse(
        access_token=access_token,
        expires_in=settings.access_token_expire_minutes * 60,
    )


# Test endpoints for role verification
@router.get("/test/viewer", dependencies=[Depends(require_viewer)])
async def test_viewer_access():
    return {"message": "Viewer access granted"}


@router.get("/test/operator", dependencies=[Depends(require_operator)])
async def test_operator_access():
    return {"message": "Operator access granted"}


@router.get("/test/admin", dependencies=[Depends(require_admin)])
async def test_admin_access():
    return {"message": "Admin access granted"}
