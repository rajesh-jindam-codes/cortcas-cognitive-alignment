from datetime import datetime, timedelta, UTC
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from app.core.config import settings

def create_token(data: dict, expires_delta: timedelta, token_type: str = "access") -> str:
    """Helper to generate JWT tokens of specified type (access/refresh)."""
    to_encode = data.copy()
    expire = datetime.now(UTC) + expires_delta
    to_encode.update({
        "exp": expire,
        "type": token_type
    })
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_access_token(subject: str, role: str, expires_delta: Optional[timedelta] = None) -> str:
    """Generate an Access Token (default 30 mins expiry)."""
    if expires_delta:
        expire = expires_delta
    else:
        expire = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    return create_token(
        data={"sub": subject, "role": role},
        expires_delta=expire,
        token_type="access"
    )

def create_refresh_token(subject: str, role: str, expires_delta: Optional[timedelta] = None) -> str:
    """Generate a Refresh Token (default 7 days expiry)."""
    if expires_delta:
        expire = expires_delta
    else:
        expire = timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
        
    return create_token(
        data={"sub": subject, "role": role},
        expires_delta=expire,
        token_type="refresh"
    )

def decode_token(token: str) -> Dict[str, Any]:
    """Decode a JWT token, verifying its signature and expiration. Raises JWTError on invalid tokens."""
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    return payload
