"""
Security Middleware - NASA/Google Standard

Purpose: Security middleware for FastAPI
Features:
- CORS configuration
- Secure headers (HSTS, CSP, X-Frame-Options, etc.)
- Request/response logging
- Audit trail
- IP blocking
"""

import time
import json
import logging
from typing import Callable, List, Optional
from pathlib import Path

from fastapi import Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


# Configure audit logger
audit_logger = logging.getLogger("audit")
audit_logger.setLevel(logging.INFO)

# Create audit log directory
audit_log_dir = Path("logs/audit")
audit_log_dir.mkdir(parents=True, exist_ok=True)

# File handler for audit logs
audit_handler = logging.FileHandler(audit_log_dir / "audit.log")
audit_handler.setFormatter(
    logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
)
audit_logger.addHandler(audit_handler)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Add security headers to all responses

    Headers:
    - Strict-Transport-Security (HSTS)
    - Content-Security-Policy (CSP)
    - X-Frame-Options
    - X-Content-Type-Options
    - X-XSS-Protection
    - Referrer-Policy
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # HSTS - Force HTTPS for 1 year
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # CSP - Restrict resource loading
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' https:; "
            "frame-ancestors 'self';"
        )

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "SAMEORIGIN"

        # Prevent MIME sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # XSS protection
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Remove server header
        response.headers.pop("Server", None)

        return response


class AuditLoggingMiddleware(BaseHTTPMiddleware):
    """
    Log all requests and responses for audit trail

    Logs:
    - Timestamp
    - User ID (from auth)
    - IP address
    - Method + Path
    - Status code
    - Response time
    - Request/response body (sanitized)
    """

    def __init__(self, app, log_request_body: bool = False, log_response_body: bool = False):
        super().__init__(app)
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()

        # Extract user info from request state (set by auth middleware)
        user_id = getattr(request.state, "user_id", "anonymous")
        role = getattr(request.state, "role", "unknown")

        # Extract client IP
        client_ip = request.client.host if request.client else "unknown"

        # Log request
        request_log = {
            "timestamp": time.time(),
            "user_id": user_id,
            "role": role,
            "ip": client_ip,
            "method": request.method,
            "path": str(request.url.path),
            "query": str(request.url.query) if request.url.query else None,
        }

        # Optionally log request body
        if self.log_request_body and request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                request_log["request_body"] = self._sanitize_body(body.decode())
            except Exception:
                request_log["request_body"] = "[failed to read]"

        # Process request
        try:
            response = await call_next(request)
        except Exception as e:
            # Log exception
            audit_logger.error(
                f"Request failed: {request.method} {request.url.path} - {str(e)}",
                extra=request_log
            )
            raise

        # Calculate response time
        elapsed_ms = (time.time() - start_time) * 1000

        # Log response
        response_log = {
            **request_log,
            "status_code": response.status_code,
            "elapsed_ms": round(elapsed_ms, 2)
        }

        # Audit log
        audit_logger.info(
            f"{request.method} {request.url.path} - {response.status_code} ({elapsed_ms:.2f}ms)",
            extra=response_log
        )

        # Add response time header
        response.headers["X-Response-Time"] = f"{elapsed_ms:.2f}ms"

        return response

    def _sanitize_body(self, body: str) -> str:
        """Sanitize sensitive data from logs"""
        try:
            data = json.loads(body)

            # Remove sensitive fields
            sensitive_fields = ["password", "api_key", "token", "secret", "private_key"]
            for field in sensitive_fields:
                if field in data:
                    data[field] = "[REDACTED]"

            return json.dumps(data)
        except Exception:
            return "[non-JSON body]"


class IPBlockingMiddleware(BaseHTTPMiddleware):
    """
    Block requests from blacklisted IPs

    Features:
    - IP blacklist
    - IP whitelist (bypass all checks)
    - Automatic blocking after N failed attempts
    """

    def __init__(
        self,
        app,
        blacklist: Optional[List[str]] = None,
        whitelist: Optional[List[str]] = None
    ):
        super().__init__(app)
        self.blacklist = set(blacklist or [])
        self.whitelist = set(whitelist or [])

        # Track failed attempts per IP
        self.failed_attempts = {}
        self.max_failed_attempts = 10
        self.block_duration = 3600  # 1 hour

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = request.client.host if request.client else None

        if not client_ip:
            return await call_next(request)

        # Check whitelist (bypass all checks)
        if client_ip in self.whitelist:
            return await call_next(request)

        # Check blacklist
        if client_ip in self.blacklist:
            audit_logger.warning(f"Blocked request from blacklisted IP: {client_ip}")
            return JSONResponse(
                status_code=403,
                content={"detail": "Access denied"}
            )

        # Check failed attempts
        if client_ip in self.failed_attempts:
            attempts, last_attempt = self.failed_attempts[client_ip]

            # Reset if block duration expired
            if time.time() - last_attempt > self.block_duration:
                del self.failed_attempts[client_ip]
            elif attempts >= self.max_failed_attempts:
                audit_logger.warning(
                    f"Blocked request from IP with too many failed attempts: {client_ip}"
                )
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Too many failed attempts. Try again later."}
                )

        # Process request
        response = await call_next(request)

        # Track failed auth attempts
        if response.status_code in [401, 403]:
            if client_ip in self.failed_attempts:
                attempts, _ = self.failed_attempts[client_ip]
                self.failed_attempts[client_ip] = (attempts + 1, time.time())
            else:
                self.failed_attempts[client_ip] = (1, time.time())

        return response


# CORS configuration
def configure_cors(app) -> None:
    """
    Configure CORS middleware

    Production:
    - Restrict origins to specific domains
    - No wildcard credentials

    Development:
    - Allow all origins (for testing)
    """
    import os

    env = os.getenv("ENV", "development")

    if env == "production":
        # Strict CORS for production
        allowed_origins = os.getenv("ALLOWED_ORIGINS", "").split(",")

        app.add_middleware(
            CORSMiddleware,
            allow_origins=allowed_origins,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "DELETE"],
            allow_headers=["Authorization", "Content-Type", "X-API-Key"],
            max_age=3600,
        )
    else:
        # Relaxed CORS for development
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )


# Environment variable protection
def validate_env_vars() -> None:
    """
    Validate required environment variables on startup

    Raises:
        RuntimeError if critical env vars are missing
    """
    import os

    required_vars = [
        # Add required env vars here
        # "DATABASE_URL",
        # "JWT_SECRET_KEY",
    ]

    recommended_vars = [
        "JWT_SECRET_KEY",
        "ALLOWED_ORIGINS",
        "ENV",
    ]

    missing_required = [var for var in required_vars if not os.getenv(var)]
    missing_recommended = [var for var in recommended_vars if not os.getenv(var)]

    if missing_required:
        raise RuntimeError(
            f"Missing required environment variables: {', '.join(missing_required)}"
        )

    if missing_recommended:
        logging.warning(
            f"Missing recommended environment variables: {', '.join(missing_recommended)}"
        )
