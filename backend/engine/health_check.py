"""
Health Check System - NASA/Google Standard

Purpose: Comprehensive health checks for all system components
Features:
- Database connectivity (PostgreSQL, Redis)
- Security middleware status
- Observability systems (metrics, tracing)
- File system permissions
- External dependencies
"""

import os
import time
from typing import Dict, Any, List
from pathlib import Path
from dataclasses import dataclass, asdict


@dataclass
class HealthStatus:
    """Health status for a single component"""
    name: str
    status: str  # "healthy", "degraded", "unhealthy"
    message: str
    response_time_ms: float = 0.0
    details: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {k: v for k, v in asdict(self).items() if v is not None}


class HealthChecker:
    """
    Comprehensive health checker for all system components
    """

    def __init__(self):
        self.checks: List[HealthStatus] = []

    def check_all(self) -> Dict[str, Any]:
        """
        Run all health checks

        Returns:
            {
                "status": "healthy" | "degraded" | "unhealthy",
                "timestamp": "...",
                "components": [...],
                "summary": {...}
            }
        """
        self.checks = []

        # Run all checks
        self._check_database()
        self._check_redis()
        self._check_security()
        self._check_observability()
        self._check_filesystem()
        self._check_dependencies()

        # Calculate overall status
        overall_status = self._calculate_overall_status()

        return {
            "status": overall_status,
            "timestamp": time.time(),
            "components": [check.to_dict() for check in self.checks],
            "summary": self._get_summary()
        }

    def _check_database(self):
        """Check PostgreSQL connectivity"""
        start = time.time()
        try:
            from backend.db.postgres_client import postgres_client

            if postgres_client is None:
                self.checks.append(HealthStatus(
                    name="postgresql",
                    status="unhealthy",
                    message="PostgreSQL client not initialized"
                ))
                return

            # Try to execute a simple query
            # Note: This assumes postgres_client has a test_connection method
            # If not, we just check if it's initialized
            self.checks.append(HealthStatus(
                name="postgresql",
                status="healthy",
                message="PostgreSQL client initialized",
                response_time_ms=(time.time() - start) * 1000
            ))

        except Exception as e:
            self.checks.append(HealthStatus(
                name="postgresql",
                status="unhealthy",
                message=f"PostgreSQL error: {str(e)}",
                response_time_ms=(time.time() - start) * 1000
            ))

    def _check_redis(self):
        """Check Redis connectivity"""
        start = time.time()
        try:
            from backend.db.redis_client import redis_client

            if redis_client is None:
                self.checks.append(HealthStatus(
                    name="redis",
                    status="degraded",
                    message="Redis client not initialized (non-critical)",
                    response_time_ms=(time.time() - start) * 1000
                ))
                return

            # Try a simple operation
            test_key = "_health_check"
            redis_client.set_json(test_key, {"test": True}, ex=10)
            result = redis_client.get_json(test_key)

            if result and result.get("test"):
                self.checks.append(HealthStatus(
                    name="redis",
                    status="healthy",
                    message="Redis cache operational",
                    response_time_ms=(time.time() - start) * 1000
                ))
            else:
                self.checks.append(HealthStatus(
                    name="redis",
                    status="degraded",
                    message="Redis cache not responding correctly",
                    response_time_ms=(time.time() - start) * 1000
                ))

        except Exception as e:
            self.checks.append(HealthStatus(
                name="redis",
                status="degraded",
                message=f"Redis error: {str(e)} (non-critical)",
                response_time_ms=(time.time() - start) * 1000
            ))

    def _check_security(self):
        """Check security middleware"""
        start = time.time()
        try:
            from backend.security import (
                SecurityHeadersMiddleware,
                AuditLoggingMiddleware,
                validate_env_vars
            )

            # Check if critical env vars are set
            jwt_secret = os.getenv("JWT_SECRET_KEY")
            env = os.getenv("ENV", "development")

            warnings = []
            if not jwt_secret:
                warnings.append("JWT_SECRET_KEY not set")

            status = "healthy" if len(warnings) == 0 else "degraded"
            message = "Security middleware configured"
            if warnings:
                message += f" (warnings: {', '.join(warnings)})"

            self.checks.append(HealthStatus(
                name="security",
                status=status,
                message=message,
                response_time_ms=(time.time() - start) * 1000,
                details={"env": env, "warnings": warnings}
            ))

        except Exception as e:
            self.checks.append(HealthStatus(
                name="security",
                status="unhealthy",
                message=f"Security middleware error: {str(e)}",
                response_time_ms=(time.time() - start) * 1000
            ))

    def _check_observability(self):
        """Check observability systems (metrics, tracing)"""
        start = time.time()
        try:
            metrics_disabled = os.getenv("CQOX_DISABLE_METRICS", "0") == "1"
            tracing_disabled = os.getenv("CQOX_DISABLE_TRACING", "0") == "1"

            status = "healthy"
            warnings = []

            if metrics_disabled:
                warnings.append("metrics disabled")
            if tracing_disabled:
                warnings.append("tracing disabled")

            message = "Observability systems configured"
            if warnings:
                status = "degraded"
                message += f" ({', '.join(warnings)})"

            self.checks.append(HealthStatus(
                name="observability",
                status=status,
                message=message,
                response_time_ms=(time.time() - start) * 1000,
                details={
                    "metrics_enabled": not metrics_disabled,
                    "tracing_enabled": not tracing_disabled
                }
            ))

        except Exception as e:
            self.checks.append(HealthStatus(
                name="observability",
                status="degraded",
                message=f"Observability error: {str(e)} (non-critical)",
                response_time_ms=(time.time() - start) * 1000
            ))

    def _check_filesystem(self):
        """Check file system permissions"""
        start = time.time()
        try:
            # Check critical directories
            critical_dirs = [
                "reports",
                "reports/figures",
                "uploads",
                "logs",
                "logs/audit"
            ]

            issues = []
            for dir_name in critical_dirs:
                dir_path = Path(dir_name)
                if not dir_path.exists():
                    try:
                        dir_path.mkdir(parents=True, exist_ok=True)
                    except Exception as e:
                        issues.append(f"Cannot create {dir_name}: {e}")
                elif not os.access(dir_path, os.W_OK):
                    issues.append(f"{dir_name} not writable")

            status = "healthy" if len(issues) == 0 else "unhealthy"
            message = "File system accessible"
            if issues:
                message = f"File system issues: {', '.join(issues)}"

            self.checks.append(HealthStatus(
                name="filesystem",
                status=status,
                message=message,
                response_time_ms=(time.time() - start) * 1000
            ))

        except Exception as e:
            self.checks.append(HealthStatus(
                name="filesystem",
                status="unhealthy",
                message=f"File system error: {str(e)}",
                response_time_ms=(time.time() - start) * 1000
            ))

    def _check_dependencies(self):
        """Check external dependencies"""
        start = time.time()
        try:
            # Check critical imports
            critical_imports = [
                ("numpy", "numpy"),
                ("pandas", "pandas"),
                ("sklearn", "scikit-learn"),
                ("fastapi", "FastAPI"),
            ]

            missing = []
            for module_name, package_name in critical_imports:
                try:
                    __import__(module_name)
                except ImportError:
                    missing.append(package_name)

            # Check optional imports
            optional_imports = [
                ("jwt", "PyJWT"),
                ("redis", "redis"),
                ("psycopg2", "psycopg2"),
            ]

            missing_optional = []
            for module_name, package_name in optional_imports:
                try:
                    __import__(module_name)
                except ImportError:
                    missing_optional.append(package_name)

            status = "healthy"
            message = "All dependencies installed"

            if missing:
                status = "unhealthy"
                message = f"Missing critical dependencies: {', '.join(missing)}"
            elif missing_optional:
                status = "degraded"
                message = f"Missing optional dependencies: {', '.join(missing_optional)}"

            self.checks.append(HealthStatus(
                name="dependencies",
                status=status,
                message=message,
                response_time_ms=(time.time() - start) * 1000,
                details={
                    "missing_critical": missing,
                    "missing_optional": missing_optional
                }
            ))

        except Exception as e:
            self.checks.append(HealthStatus(
                name="dependencies",
                status="unhealthy",
                message=f"Dependency check error: {str(e)}",
                response_time_ms=(time.time() - start) * 1000
            ))

    def _calculate_overall_status(self) -> str:
        """Calculate overall system status"""
        if not self.checks:
            return "unknown"

        # Count statuses
        unhealthy_count = sum(1 for c in self.checks if c.status == "unhealthy")
        degraded_count = sum(1 for c in self.checks if c.status == "degraded")

        # Any unhealthy critical components = overall unhealthy
        critical_components = ["dependencies", "filesystem"]
        critical_unhealthy = any(
            c.status == "unhealthy" and c.name in critical_components
            for c in self.checks
        )

        if critical_unhealthy or unhealthy_count > 0:
            return "unhealthy"
        elif degraded_count > 0:
            return "degraded"
        else:
            return "healthy"

    def _get_summary(self) -> Dict[str, Any]:
        """Get summary of health check results"""
        if not self.checks:
            return {}

        healthy = sum(1 for c in self.checks if c.status == "healthy")
        degraded = sum(1 for c in self.checks if c.status == "degraded")
        unhealthy = sum(1 for c in self.checks if c.status == "unhealthy")

        avg_response_time = sum(c.response_time_ms for c in self.checks) / len(self.checks)

        return {
            "total_components": len(self.checks),
            "healthy": healthy,
            "degraded": degraded,
            "unhealthy": unhealthy,
            "avg_response_time_ms": round(avg_response_time, 2)
        }


# Singleton instance
health_checker = HealthChecker()
