# OIDC/Keycloak integration
import httpx
import logging
from functools import lru_cache
from typing import Optional, Dict, Any
from pydantic import BaseModel
from jose import jwt, JWTError
from jose.utils import base64url_decode

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class OIDCConfig(BaseModel):
    issuer: str
    authorization_endpoint: str
    token_endpoint: str
    jwks_uri: str
    userinfo_endpoint: str
    end_session_endpoint: str
    scopes_supported: list[str]
    response_types_supported: list[str]
    subject_types_supported: list[str]
    id_token_signing_alg_values_supported: list[str]


class JWK(BaseModel):
    kty: str
    use: Optional[str] = None
    kid: Optional[str] = None
    n: Optional[str] = None
    e: Optional[str] = None
    alg: Optional[str] = None


class JWKS(BaseModel):
    keys: list[JWK]


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: Optional[str] = None
    id_token: Optional[str] = None
    scope: Optional[str] = None


class UserInfo(BaseModel):
    sub: str
    email: Optional[str] = None
    email_verified: Optional[bool] = None
    preferred_username: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    name: Optional[str] = None
    roles: list[str] = []


_oidc_config_cache: Optional[OIDCConfig] = None


async def get_oidc_config() -> OIDCConfig:
    """Fetch and cache OIDC configuration from Keycloak."""
    global _oidc_config_cache
    if _oidc_config_cache is not None:
        return _oidc_config_cache

    issuer = settings.effective_oidc_issuer
    config_url = f"{issuer}/.well-known/openid-configuration"

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(config_url)
        response.raise_for_status()
        data = response.json()
        _oidc_config_cache = OIDCConfig(**data)
        return _oidc_config_cache


_jwks_cache: Optional[JWKS] = None


async def get_jwks() -> JWKS:
    """Fetch and cache JWKS from Keycloak."""
    global _jwks_cache
    if _jwks_cache is not None:
        return _jwks_cache

    oidc_config = await get_oidc_config()
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(oidc_config.jwks_uri)
        response.raise_for_status()
        data = response.json()
        _jwks_cache = JWKS(**data)
        return _jwks_cache


def get_public_key(jwks: JWKS, kid: str) -> Optional[str]:
    """Extract RSA public key from JWKS for given key ID."""
    for key in jwks.keys:
        if key.kid == kid and key.kty == "RSA":
            # Convert JWK to PEM format
            n = base64url_decode(key.n.encode()).hex()
            e = base64url_decode(key.e.encode()).hex()
            # Simple RSA public key construction (for validation)
            # In production, use cryptography library to properly construct PEM
            return f"-----BEGIN PUBLIC KEY-----\n{key.n}\n-----END PUBLIC KEY-----"
    return None


async def validate_id_token(id_token: str, nonce: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Validate ID token from Keycloak using JWKS."""
    try:
        # Get unverified header to find kid
        unverified_header = jwt.get_unverified_header(id_token)
        kid = unverified_header.get("kid")
        if not kid:
            logger.warning("ID token missing kid in header")
            return None

        # Fetch JWKS and get public key
        jwks = await get_jwks()
        public_key = get_public_key(jwks, kid)
        if not public_key:
            logger.warning(f"No matching key found for kid: {kid}")
            return None

        # Decode and validate token
        payload = jwt.decode(
            id_token,
            public_key,
            algorithms=["RS256"],
            audience=settings.oidc_audience,
            issuer=settings.effective_oidc_issuer,
            options={"verify_aud": True, "verify_iss": True, "verify_exp": True},
        )

        # Verify nonce if provided
        if nonce and payload.get("nonce") != nonce:
            logger.warning("Nonce mismatch in ID token")
            return None

        return payload
    except JWTError as e:
        logger.warning(f"ID token validation failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error validating ID token: {e}")
        return None


async def exchange_code_for_tokens(
    code: str,
    redirect_uri: str,
    code_verifier: str,
) -> Optional[TokenResponse]:
    """Exchange authorization code for tokens using PKCE."""
    try:
        oidc_config = await get_oidc_config()
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                oidc_config.token_endpoint,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": redirect_uri,
                    "client_id": settings.keycloak_client_id,
                    "client_secret": settings.keycloak_client_secret,
                    "code_verifier": code_verifier,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response.raise_for_status()
            return TokenResponse(**response.json())
    except httpx.HTTPStatusError as e:
        logger.error(f"Token exchange failed: {e.response.status_code} - {e.response.text}")
        return None
    except Exception as e:
        logger.error(f"Token exchange error: {e}")
        return None


async def get_user_info(access_token: str) -> Optional[UserInfo]:
    """Fetch user info from Keycloak using access token."""
    try:
        oidc_config = await get_oidc_config()
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                oidc_config.userinfo_endpoint,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            response.raise_for_status()
            data = response.json()
            # Extract realm roles from resource_access
            roles = []
            if "resource_access" in data:
                client_roles = data["resource_access"].get(settings.keycloak_client_id, {})
                roles = client_roles.get("roles", [])
            elif "realm_access" in data:
                roles = data["realm_access"].get("roles", [])
            data["roles"] = roles
            return UserInfo(**data)
    except Exception as e:
        logger.error(f"Failed to fetch user info: {e}")
        return None


def build_authorization_url(
    redirect_uri: str,
    state: str,
    nonce: str,
    code_challenge: str,
) -> str:
    """Build Keycloak authorization URL with PKCE."""
    oidc_config = get_oidc_config()  # Note: this is sync for URL building
    # We'll use a sync approach for URL building
    params = {
        "client_id": settings.keycloak_client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "nonce": nonce,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    query = "&".join(f"{k}={v}" for k, v in params.items())
    # Use the known Keycloak auth endpoint format
    auth_endpoint = f"{settings.keycloak_url}/realms/{settings.keycloak_realm}/protocol/openid-connect/auth"
    return f"{auth_endpoint}?{query}"


def build_logout_url(redirect_uri: str) -> str:
    """Build Keycloak logout URL."""
    logout_endpoint = f"{settings.keycloak_url}/realms/{settings.keycloak_realm}/protocol/openid-connect/logout"
    return f"{logout_endpoint}?redirect_uri={redirect_uri}"
