"""
Prometheus Metrics - NASA/Google Standard

Purpose: Application metrics collection for Prometheus
Features:
- Request metrics (count, latency, errors)
- Business metrics (jobs, estimators, policies)
- Database metrics (connection pool, query time)
- Custom metrics
"""

import time
import os
from typing import Callable
from functools import wraps

from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    Summary,
    Info,
    generate_latest,
    REGISTRY
)
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


# ===== HTTP Metrics =====

# Request count
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

# Request latency
http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint'],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0)
)

# Request size
http_request_size_bytes = Summary(
    'http_request_size_bytes',
    'HTTP request size in bytes',
    ['method', 'endpoint']
)

# Response size
http_response_size_bytes = Summary(
    'http_response_size_bytes',
    'HTTP response size in bytes',
    ['method', 'endpoint']
)

# Active requests
http_requests_in_progress = Gauge(
    'http_requests_in_progress',
    'Number of HTTP requests in progress',
    ['method', 'endpoint']
)


# ===== Business Metrics =====

# Jobs
jobs_created_total = Counter(
    'jobs_created_total',
    'Total jobs created',
    ['dataset_id']
)

jobs_completed_total = Counter(
    'jobs_completed_total',
    'Total jobs completed',
    ['dataset_id', 'status']
)

jobs_duration_seconds = Histogram(
    'jobs_duration_seconds',
    'Job execution duration',
    ['dataset_id'],
    buckets=(1, 5, 10, 30, 60, 120, 300, 600, 1800, 3600)
)

jobs_active = Gauge(
    'jobs_active',
    'Number of active jobs'
)

# Estimators
estimator_runs_total = Counter(
    'estimator_runs_total',
    'Total estimator runs',
    ['estimator_name', 'status']
)

estimator_duration_seconds = Histogram(
    'estimator_duration_seconds',
    'Estimator execution duration',
    ['estimator_name'],
    buckets=(0.1, 0.5, 1, 2, 5, 10, 30, 60, 120)
)

# Policies
policies_created_total = Counter(
    'policies_created_total',
    'Total policies created'
)

policies_optimized_total = Counter(
    'policies_optimized_total',
    'Total policy optimizations',
    ['objective']
)

# Quality Gates
quality_gates_total = Counter(
    'quality_gates_total',
    'Total quality gate checks',
    ['gate_name', 'status']
)


# ===== Database Metrics =====

db_connections_active = Gauge(
    'db_connections_active',
    'Active database connections'
)

db_connections_idle = Gauge(
    'db_connections_idle',
    'Idle database connections'
)

db_query_duration_seconds = Histogram(
    'db_query_duration_seconds',
    'Database query duration',
    ['query_type'],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0)
)

db_queries_total = Counter(
    'db_queries_total',
    'Total database queries',
    ['query_type', 'status']
)


# ===== System Metrics =====

app_info = Info(
    'cqox_app',
    'CQOx application info'
)

# Set app info
app_info.info({
    'version': os.getenv('APP_VERSION', '1.0.0'),
    'environment': os.getenv('ENVIRONMENT', 'development'),
    'port': os.getenv('PORT', '8080')
})


# ===== Middleware =====

class PrometheusMetricsMiddleware(BaseHTTPMiddleware):
    """
    Prometheus metrics middleware

    Automatically tracks:
    - Request count
    - Request latency
    - Request/response size
    - Active requests
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Extract endpoint (remove query params, IDs)
        endpoint = self._normalize_endpoint(request.url.path)
        method = request.method

        # Track request size
        content_length = request.headers.get('content-length', 0)
        if content_length:
            http_request_size_bytes.labels(method=method, endpoint=endpoint).observe(int(content_length))

        # Track active requests
        http_requests_in_progress.labels(method=method, endpoint=endpoint).inc()

        # Measure latency
        start_time = time.time()

        try:
            response = await call_next(request)
            status_code = response.status_code

        except Exception as e:
            # Track errors
            http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status_code=500
            ).inc()

            http_requests_in_progress.labels(method=method, endpoint=endpoint).dec()
            raise

        finally:
            # Record latency
            duration = time.time() - start_time
            http_request_duration_seconds.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)

        # Track request count
        http_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status_code=status_code
        ).inc()

        # Track response size
        response_size = response.headers.get('content-length', 0)
        if response_size:
            http_response_size_bytes.labels(method=method, endpoint=endpoint).observe(int(response_size))

        # Decrease active requests
        http_requests_in_progress.labels(method=method, endpoint=endpoint).dec()

        return response

    def _normalize_endpoint(self, path: str) -> str:
        """
        Normalize endpoint for metrics

        Convert /api/jobs/abc123 -> /api/jobs/{id}
        """
        parts = path.split('/')

        normalized = []
        for i, part in enumerate(parts):
            # Replace UUIDs and numeric IDs with {id}
            if part and (self._is_uuid(part) or self._is_numeric_id(part)):
                normalized.append('{id}')
            else:
                normalized.append(part)

        return '/'.join(normalized)

    @staticmethod
    def _is_uuid(s: str) -> bool:
        """Check if string is UUID"""
        import re
        uuid_pattern = re.compile(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$', re.I)
        return bool(uuid_pattern.match(s))

    @staticmethod
    def _is_numeric_id(s: str) -> bool:
        """Check if string is numeric ID"""
        return s.isdigit() and len(s) < 20


# ===== Decorators =====

def track_job_execution(func: Callable) -> Callable:
    """
    Decorator to track job execution metrics

    Usage:
        @track_job_execution
        async def run_job(job_id, dataset_id):
            ...
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        dataset_id = kwargs.get('dataset_id', 'unknown')

        # Increment job counter
        jobs_created_total.labels(dataset_id=dataset_id).inc()
        jobs_active.inc()

        start_time = time.time()
        status = 'completed'

        try:
            result = await func(*args, **kwargs)
            return result

        except Exception as e:
            status = 'failed'
            raise

        finally:
            # Record duration
            duration = time.time() - start_time
            jobs_duration_seconds.labels(dataset_id=dataset_id).observe(duration)

            # Record completion
            jobs_completed_total.labels(dataset_id=dataset_id, status=status).inc()
            jobs_active.dec()

    return wrapper


def track_estimator_run(estimator_name: str) -> Callable:
    """
    Decorator to track estimator execution

    Usage:
        @track_estimator_run("DifferenceInDifferences")
        def run_estimator(data):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            status = 'success'

            try:
                result = func(*args, **kwargs)
                return result

            except Exception:
                status = 'failed'
                raise

            finally:
                # Record duration
                duration = time.time() - start_time
                estimator_duration_seconds.labels(estimator_name=estimator_name).observe(duration)

                # Record run
                estimator_runs_total.labels(estimator_name=estimator_name, status=status).inc()

        return wrapper
    return decorator


def track_db_query(query_type: str = "select") -> Callable:
    """
    Decorator to track database query metrics

    Usage:
        @track_db_query("select")
        def get_jobs():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            status = 'success'

            try:
                result = func(*args, **kwargs)
                return result

            except Exception:
                status = 'failed'
                raise

            finally:
                # Record duration
                duration = time.time() - start_time
                db_query_duration_seconds.labels(query_type=query_type).observe(duration)

                # Record query
                db_queries_total.labels(query_type=query_type, status=status).inc()

        return wrapper
    return decorator


# ===== Metrics Endpoint =====

def get_metrics() -> bytes:
    """
    Get Prometheus metrics in text format

    Usage in FastAPI:
        @app.get("/metrics")
        def metrics():
            return Response(content=get_metrics(), media_type="text/plain")
    """
    return generate_latest(REGISTRY)


# ===== Utility Functions =====

def update_db_connection_metrics(pool_status: dict):
    """
    Update database connection pool metrics

    Args:
        pool_status: Dictionary with 'active' and 'idle' counts
    """
    db_connections_active.set(pool_status.get('active', 0))
    db_connections_idle.set(pool_status.get('idle', 0))


def record_quality_gate(gate_name: str, passed: bool):
    """
    Record quality gate check

    Args:
        gate_name: Name of quality gate
        passed: Whether gate passed
    """
    status = 'passed' if passed else 'failed'
    quality_gates_total.labels(gate_name=gate_name, status=status).inc()


def record_policy_optimization(objective: str = "profit"):
    """Record policy optimization"""
    policies_optimized_total.labels(objective=objective).inc()
