"""
Security Module - NASA/Google Standard

Purpose: Authentication, authorization, and security middleware
"""

from backend.security.auth import (
    APIKeyAuth,
    JWTAuth,
    RoleChecker,
    ScopeChecker,
    TokenData,
    api_key_auth,
    jwt_auth,
    require_admin,
    require_analyst,
    require_user,
    require_write,
    require_read,
    generate_api_key,
    revoke_api_key,
)

from backend.security.middleware import (
    SecurityHeadersMiddleware,
    AuditLoggingMiddleware,
    IPBlockingMiddleware,
    configure_cors,
    validate_env_vars,
)

__all__ = [
    # Auth
    "APIKeyAuth",
    "JWTAuth",
    "RoleChecker",
    "ScopeChecker",
    "TokenData",
    "api_key_auth",
    "jwt_auth",
    "require_admin",
    "require_analyst",
    "require_user",
    "require_write",
    "require_read",
    "generate_api_key",
    "revoke_api_key",
    # Middleware
    "SecurityHeadersMiddleware",
    "AuditLoggingMiddleware",
    "IPBlockingMiddleware",
    "configure_cors",
    "validate_env_vars",
]
