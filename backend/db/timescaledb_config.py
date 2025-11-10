"""
TimescaleDB Configuration - NASA/Google Standard

Purpose: Time-series optimized database configuration
Features:
- Hypertable creation for time-series data
- Automatic partitioning by time
- Data retention policies
- Compression policies
- Continuous aggregates
"""

import os
from typing import Optional
from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool
import logging

logger = logging.getLogger(__name__)


class TimescaleDBConfig:
    """TimescaleDB configuration and setup"""

    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or os.getenv(
            "DATABASE_URL",
            "postgresql://cqox_user:changeme@localhost:5432/cqox_db"
        )

        # Connection pool settings
        self.pool_size = int(os.getenv("DB_POOL_SIZE", "20"))
        self.max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "10"))
        self.pool_timeout = int(os.getenv("DB_POOL_TIMEOUT", "30"))
        self.pool_recycle = int(os.getenv("DB_POOL_RECYCLE", "3600"))

        # TimescaleDB settings
        self.retention_days = int(os.getenv("TIMESCALE_RETENTION_DAYS", "90"))
        self.chunk_interval = os.getenv("TIMESCALE_CHUNK_INTERVAL", "7 days")

        self.engine = None

    def create_engine_with_pool(self):
        """Create SQLAlchemy engine with connection pooling"""
        self.engine = create_engine(
            self.database_url,
            poolclass=QueuePool,
            pool_size=self.pool_size,
            max_overflow=self.max_overflow,
            pool_timeout=self.pool_timeout,
            pool_recycle=self.pool_recycle,
            pool_pre_ping=True,  # Test connections before using
            echo=False
        )
        return self.engine

    def setup_timescaledb(self):
        """Setup TimescaleDB extension and hypertables"""
        if not self.engine:
            self.create_engine_with_pool()

        with self.engine.connect() as conn:
            # Enable TimescaleDB extension
            logger.info("Enabling TimescaleDB extension...")
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;"))
            conn.commit()

            # Create hypertables for time-series data
            self._create_hypertables(conn)

            # Set up retention policies
            self._setup_retention_policies(conn)

            # Set up compression policies
            self._setup_compression_policies(conn)

            # Create continuous aggregates
            self._create_continuous_aggregates(conn)

            logger.info("TimescaleDB setup completed successfully")

    def _create_hypertables(self, conn):
        """Create hypertables for time-series tables"""

        # Jobs table as hypertable
        logger.info("Creating hypertable: jobs")
        conn.execute(text("""
            SELECT create_hypertable(
                'jobs',
                'created_at',
                chunk_time_interval => INTERVAL :chunk_interval,
                if_not_exists => TRUE
            );
        """), {"chunk_interval": self.chunk_interval})

        # Estimator results as hypertable
        logger.info("Creating hypertable: estimator_results")
        conn.execute(text("""
            SELECT create_hypertable(
                'estimator_results',
                'created_at',
                chunk_time_interval => INTERVAL :chunk_interval,
                if_not_exists => TRUE
            );
        """), {"chunk_interval": self.chunk_interval})

        # Quality gates as hypertable
        logger.info("Creating hypertable: quality_gates")
        conn.execute(text("""
            SELECT create_hypertable(
                'quality_gates',
                'created_at',
                chunk_time_interval => INTERVAL :chunk_interval,
                if_not_exists => TRUE
            );
        """), {"chunk_interval": self.chunk_interval})

        # Metrics as hypertable
        logger.info("Creating hypertable: metrics")
        conn.execute(text("""
            SELECT create_hypertable(
                'metrics',
                'timestamp',
                chunk_time_interval => INTERVAL :chunk_interval,
                if_not_exists => TRUE
            );
        """), {"chunk_interval": self.chunk_interval})

        conn.commit()

    def _setup_retention_policies(self, conn):
        """Setup data retention policies"""
        logger.info(f"Setting up retention policies ({self.retention_days} days)...")

        tables = ['jobs', 'estimator_results', 'quality_gates', 'metrics']

        for table in tables:
            # Drop existing policy if exists
            conn.execute(text(f"""
                SELECT remove_retention_policy('{table}', if_exists => true);
            """))

            # Add new retention policy
            conn.execute(text(f"""
                SELECT add_retention_policy(
                    '{table}',
                    INTERVAL '{self.retention_days} days'
                );
            """))

        conn.commit()
        logger.info("Retention policies configured")

    def _setup_compression_policies(self, conn):
        """Setup compression policies for old data"""
        logger.info("Setting up compression policies...")

        tables = ['jobs', 'estimator_results', 'quality_gates', 'metrics']

        for table in tables:
            # Enable compression
            conn.execute(text(f"""
                ALTER TABLE {table} SET (
                    timescaledb.compress,
                    timescaledb.compress_orderby = 'created_at DESC'
                );
            """))

            # Add compression policy (compress data older than 7 days)
            conn.execute(text(f"""
                SELECT add_compression_policy(
                    '{table}',
                    INTERVAL '7 days',
                    if_not_exists => true
                );
            """))

        conn.commit()
        logger.info("Compression policies configured")

    def _create_continuous_aggregates(self, conn):
        """Create continuous aggregates for faster queries"""
        logger.info("Creating continuous aggregates...")

        # Daily job statistics
        conn.execute(text("""
            CREATE MATERIALIZED VIEW IF NOT EXISTS jobs_daily
            WITH (timescaledb.continuous) AS
            SELECT
                time_bucket('1 day', created_at) AS bucket,
                COUNT(*) as total_jobs,
                COUNT(*) FILTER (WHERE status = 'completed') as completed_jobs,
                COUNT(*) FILTER (WHERE status = 'failed') as failed_jobs,
                AVG(EXTRACT(EPOCH FROM (updated_at - created_at))) as avg_duration_seconds
            FROM jobs
            GROUP BY bucket;
        """))

        # Add refresh policy
        conn.execute(text("""
            SELECT add_continuous_aggregate_policy(
                'jobs_daily',
                start_offset => INTERVAL '3 days',
                end_offset => INTERVAL '1 hour',
                schedule_interval => INTERVAL '1 hour',
                if_not_exists => true
            );
        """))

        conn.commit()
        logger.info("Continuous aggregates created")

    def create_indexes(self, conn):
        """Create optimized indexes"""
        logger.info("Creating optimized indexes...")

        # Jobs table indexes
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_jobs_dataset_id ON jobs(dataset_id);
            CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
            CREATE INDEX IF NOT EXISTS idx_jobs_created_at_desc ON jobs(created_at DESC);
        """))

        # Estimator results indexes
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_estimator_results_job_id ON estimator_results(job_id);
            CREATE INDEX IF NOT EXISTS idx_estimator_results_estimator_name ON estimator_results(estimator_name);
        """))

        # Quality gates indexes
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_quality_gates_job_id ON quality_gates(job_id);
            CREATE INDEX IF NOT EXISTS idx_quality_gates_gate_name ON quality_gates(gate_name);
        """))

        # Composite indexes for common queries
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_jobs_dataset_status
            ON jobs(dataset_id, status, created_at DESC);
        """))

        conn.commit()
        logger.info("Indexes created successfully")


# Singleton instance
timescaledb_config = TimescaleDBConfig()


def initialize_timescaledb():
    """Initialize TimescaleDB with all configurations"""
    try:
        timescaledb_config.setup_timescaledb()

        with timescaledb_config.engine.connect() as conn:
            timescaledb_config.create_indexes(conn)

        logger.info("✓ TimescaleDB initialized successfully")
        return True
    except Exception as e:
        logger.error(f"✗ TimescaleDB initialization failed: {e}")
        return False
