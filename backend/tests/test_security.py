# Security utility tests
import pytest
from app.core.security import (
    create_access_token,
    decode_token,
    generate_pkce_pair,
    hash_token,
    verify_password,
    get_password_hash,
    TokenData,
)


def test_create_and_decode_token():
    data = {"sub": "user123", "email": "test@example.com", "roles": ["viewer"]}
    token = create_access_token(data)
    
    decoded = decode_token(token)
    assert decoded is not None
    assert decoded.sub == "user123"
    assert decoded.email == "test@example.com"
    assert decoded.roles == ["viewer"]
    assert decoded.exp > 0
    assert decoded.iat > 0


def test_decode_invalid_token():
    decoded = decode_token("invalid.token.string")
    assert decoded is None


def test_decode_expired_token():
    # Create token with negative expiry (expired)
    import time
    from jose import jwt
    from app.core.config import get_settings
    
    settings = get_settings()
    payload = {"sub": "user123", "exp": int(time.time()) - 3600, "iat": int(time.time()) - 7200}
    token = jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
    
    decoded = decode_token(token)
    assert decoded is None


def test_hash_token():
    token = "test-token-123"
    hashed = hash_token(token)
    assert len(hashed) == 64  # SHA256 hex
    assert hashed == hash_token(token)  # Deterministic


def test_password_hash_and_verify():
    password = "secure-password-123"
    hashed = get_password_hash(password)
    
    assert verify_password(password, hashed)
    assert not verify_password("wrong-password", hashed)


def test_generate_pkce_pair():
    verifier, challenge = generate_pkce_pair()
    assert len(verifier) > 20
    assert len(challenge) > 20
    assert verifier != challenge


def test_token_data_model():
    data = TokenData(
        sub="user123",
        email="test@example.com",
        roles=["viewer", "operator"],
        exp=1234567890,
        iat=1234567000,
        nonce="abc123",
    )
    assert data.sub == "user123"
    assert "viewer" in data.roles
    assert data.nonce == "abc123"