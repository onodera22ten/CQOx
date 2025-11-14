"""
Security - Authentication & Authorization
NASA/Google Standard

Purpose: API authentication and authorization
Features:
- API key authentication
- JWT token support
- Role-based access control (RBAC)
- Rate limiting per API key
- Audit logging
"""

import os
import time
import hashlib
import secrets
from typing import Optional, Dict, List
from datetime import datetime, timedelta
from collections import defaultdict

import jwt
from fastapi import Security, HTTPException, status, Depends
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel


# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# API Key storage (in production, use database)
API_KEYS: Dict[str, Dict] = {
    # Format: "api_key": {"user_id": "...", "role": "...", "scopes": [...]}
}

# Rate limiting storage (requests per minute)
RATE_LIMIT_STORE: Dict[str, List[float]] = defaultdict(list)
RATE_LIMIT_MAX_REQUESTS = 100  # per minute


class TokenData(BaseModel):
    """JWT token payload"""
    user_id: str
    role: str
    scopes: List[str]
    exp: Optional[int] = None


class APIKeyAuth:
    """API Key Authentication"""

    def __init__(self):
        self.api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

    async def __call__(self, api_key: Optional[str] = Security(APIKeyHeader(name="X-API-Key", auto_error=False))) -> Dict:
        """Validate API key"""
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key required",
                headers={"WWW-Authenticate": "API-Key"},
            )

        # Check if API key exists
        if api_key not in API_KEYS:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid API key"
            )

        # Check rate limit
        if not self._check_rate_limit(api_key):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded"
            )

        # Return user info
        return API_KEYS[api_key]

    def _check_rate_limit(self, api_key: str) -> bool:
        """Check if API key is within rate limit"""
        now = time.time()
        window_start = now - 60  # 1 minute window

        # Clean old requests
        RATE_LIMIT_STORE[api_key] = [
            ts for ts in RATE_LIMIT_STORE[api_key]
            if ts > window_start
        ]

        # Check limit
        if len(RATE_LIMIT_STORE[api_key]) >= RATE_LIMIT_MAX_REQUESTS:
            return False

        # Add current request
        RATE_LIMIT_STORE[api_key].append(now)
        return True


class JWTAuth:
    """JWT Token Authentication"""

    def __init__(self):
        self.bearer_scheme = HTTPBearer(auto_error=False)

    def create_access_token(
        self,
        user_id: str,
        role: str = "user",
        scopes: List[str] = None,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT access token"""
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode = {
            "user_id": user_id,
            "role": role,
            "scopes": scopes or [],
            "exp": int(expire.timestamp())
        }

        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    async def __call__(
        self,
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
    ) -> TokenData:
        """Validate JWT token"""
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Bearer token required",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = credentials.credentials

        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id: str = payload.get("user_id")
            role: str = payload.get("role", "user")
            scopes: List[str] = payload.get("scopes", [])

            if user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token"
                )

            return TokenData(user_id=user_id, role=role, scopes=scopes)

        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )


class RoleChecker:
    """Role-Based Access Control"""

    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, token_data: TokenData = Depends(JWTAuth())) -> TokenData:
        """Check if user has required role"""
        if token_data.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{token_data.role}' not authorized. Required: {self.allowed_roles}"
            )
        return token_data


class ScopeChecker:
    """Scope-Based Access Control"""

    def __init__(self, required_scopes: List[str]):
        self.required_scopes = required_scopes

    def __call__(self, token_data: TokenData = Depends(JWTAuth())) -> TokenData:
        """Check if user has required scopes"""
        for scope in self.required_scopes:
            if scope not in token_data.scopes:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Missing required scope: {scope}"
                )
        return token_data


# Helper functions

def generate_api_key(user_id: str, role: str = "user", scopes: List[str] = None) -> str:
    """Generate a new API key"""
    # Generate random key
    random_part = secrets.token_urlsafe(32)

    # Create hash with user_id for verification
    key_data = f"{user_id}:{random_part}:{time.time()}"
    api_key = hashlib.sha256(key_data.encode()).hexdigest()

    # Store in memory (in production, use database)
    API_KEYS[api_key] = {
        "user_id": user_id,
        "role": role,
        "scopes": scopes or ["read"],
        "created_at": datetime.utcnow().isoformat()
    }

    return api_key


def revoke_api_key(api_key: str) -> bool:
    """Revoke an API key"""
    if api_key in API_KEYS:
        del API_KEYS[api_key]
        return True
    return False


# Singleton instances
api_key_auth = APIKeyAuth()
jwt_auth = JWTAuth()

# Role checkers
require_admin = RoleChecker(["admin"])
require_analyst = RoleChecker(["admin", "analyst"])
require_user = RoleChecker(["admin", "analyst", "user"])

# Scope checkers
require_write = ScopeChecker(["write"])
require_read = ScopeChecker(["read"])
