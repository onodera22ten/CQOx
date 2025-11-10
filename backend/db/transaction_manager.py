"""
Transaction Manager - NASA/Google Standard

Purpose: Advanced transaction management with retry logic and deadlock handling
Features:
- Context manager for transactions
- Automatic retry on deadlock
- Savepoints support
- Nested transactions
- Connection pooling integration
"""

import time
import functools
from contextlib import contextmanager
from typing import Optional, Callable, Any
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.exc import OperationalError, IntegrityError, DBAPIError
import logging

logger = logging.getLogger(__name__)


class TransactionManager:
    """
    Advanced transaction management

    Features:
    - Automatic retry on transient errors
    - Deadlock detection and retry
    - Savepoint management
    - Connection health checks
    """

    def __init__(self, engine):
        self.engine = engine
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine
        )

    @contextmanager
    def transaction(
        self,
        max_retries: int = 3,
        retry_delay: float = 0.1,
        isolation_level: Optional[str] = None
    ):
        """
        Context manager for transactions with automatic retry

        Args:
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries (seconds)
            isolation_level: Transaction isolation level

        Usage:
            with transaction_manager.transaction() as session:
                session.add(obj)
                # commit happens automatically
        """
        session = self.SessionLocal()

        if isolation_level:
            session.connection(execution_options={"isolation_level": isolation_level})

        retries = 0
        while retries <= max_retries:
            try:
                yield session
                session.commit()
                break

            except (OperationalError, DBAPIError) as e:
                session.rollback()

                # Check if it's a retryable error (deadlock, connection lost, etc.)
                if self._is_retryable_error(e) and retries < max_retries:
                    retries += 1
                    wait_time = retry_delay * (2 ** retries)  # Exponential backoff
                    logger.warning(
                        f"Transaction failed (attempt {retries}/{max_retries}), "
                        f"retrying in {wait_time}s... Error: {e}"
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(f"Transaction failed after {retries} retries: {e}")
                    raise

            except IntegrityError as e:
                session.rollback()
                logger.error(f"Integrity error (not retrying): {e}")
                raise

            except Exception as e:
                session.rollback()
                logger.error(f"Unexpected error in transaction: {e}")
                raise

            finally:
                if retries > max_retries or session.is_active is False:
                    session.close()

    @contextmanager
    def savepoint(self, session: Session, name: str):
        """
        Create a savepoint within a transaction

        Usage:
            with transaction_manager.transaction() as session:
                session.add(obj1)

                with transaction_manager.savepoint(session, "sp1"):
                    session.add(obj2)
                    # Will rollback to sp1 on error

                session.add(obj3)
        """
        savepoint = session.begin_nested()
        try:
            yield session
            savepoint.commit()
        except Exception as e:
            logger.warning(f"Rolling back to savepoint '{name}': {e}")
            savepoint.rollback()
            raise

    def _is_retryable_error(self, error: Exception) -> bool:
        """Check if error is retryable (deadlock, connection lost, etc.)"""
        error_msg = str(error).lower()

        retryable_patterns = [
            "deadlock",
            "lock wait timeout",
            "connection",
            "timeout",
            "database is locked",
            "could not serialize",
            "canceling statement due to conflict"
        ]

        return any(pattern in error_msg for pattern in retryable_patterns)

    def execute_with_retry(
        self,
        func: Callable,
        *args,
        max_retries: int = 3,
        retry_delay: float = 0.1,
        **kwargs
    ) -> Any:
        """
        Execute a function with automatic retry on transient errors

        Usage:
            def insert_data(session, data):
                session.add(data)
                session.commit()

            transaction_manager.execute_with_retry(insert_data, session, data)
        """
        retries = 0
        last_error = None

        while retries <= max_retries:
            try:
                return func(*args, **kwargs)

            except (OperationalError, DBAPIError) as e:
                last_error = e

                if self._is_retryable_error(e) and retries < max_retries:
                    retries += 1
                    wait_time = retry_delay * (2 ** retries)
                    logger.warning(
                        f"Function execution failed (attempt {retries}/{max_retries}), "
                        f"retrying in {wait_time}s..."
                    )
                    time.sleep(wait_time)
                else:
                    raise

            except Exception as e:
                logger.error(f"Non-retryable error: {e}")
                raise

        # If all retries failed
        raise last_error


def transactional(
    max_retries: int = 3,
    retry_delay: float = 0.1,
    isolation_level: Optional[str] = None
):
    """
    Decorator for automatic transaction management

    Usage:
        @transactional(max_retries=3)
        def create_job(session, dataset_id, mapping):
            job = Job(dataset_id=dataset_id, mapping=mapping)
            session.add(job)
            return job
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Assume first argument is session or self
            session = args[0] if args else None

            if not isinstance(session, Session):
                # If not a session, execute normally
                return func(*args, **kwargs)

            retries = 0
            last_error = None

            while retries <= max_retries:
                try:
                    if isolation_level:
                        session.connection(execution_options={"isolation_level": isolation_level})

                    result = func(*args, **kwargs)
                    session.commit()
                    return result

                except (OperationalError, DBAPIError) as e:
                    session.rollback()
                    last_error = e

                    error_msg = str(e).lower()
                    is_retryable = any(
                        pattern in error_msg
                        for pattern in ["deadlock", "lock wait", "connection", "timeout"]
                    )

                    if is_retryable and retries < max_retries:
                        retries += 1
                        wait_time = retry_delay * (2 ** retries)
                        logger.warning(f"Retrying transaction (attempt {retries}/{max_retries})...")
                        time.sleep(wait_time)
                    else:
                        raise

                except Exception as e:
                    session.rollback()
                    raise

            raise last_error

        return wrapper
    return decorator


# Connection health check

def check_connection_health(engine) -> bool:
    """Check database connection health"""
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Connection health check failed: {e}")
        return False
