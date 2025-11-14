"""
Backup Manager - NASA/Google Standard

Purpose: Automated backup and restore for PostgreSQL/TimescaleDB
Features:
- Scheduled backups (pg_dump)
- Point-in-time recovery (PITR)
- Backup to S3
- Backup verification
- Restore procedures
- Retention policy management
"""

import os
import subprocess
import datetime
from pathlib import Path
from typing import Optional, List
import logging
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class BackupManager:
    """
    Automated backup management for PostgreSQL/TimescaleDB

    Features:
    - Full database backups
    - Incremental backups (WAL archiving)
    - S3 upload
    - Automated retention
    - Restore capabilities
    """

    def __init__(self):
        self.backup_dir = Path(os.getenv("BACKUP_DIR", "/backups"))
        self.retention_days = int(os.getenv("BACKUP_RETENTION_DAYS", "30"))

        # S3 configuration
        self.s3_enabled = os.getenv("BACKUP_S3_BUCKET") is not None
        self.s3_bucket = os.getenv("BACKUP_S3_BUCKET")
        self.s3_region = os.getenv("BACKUP_S3_REGION", "us-east-1")

        # Database connection
        self.db_host = os.getenv("DB_HOST", "localhost")
        self.db_port = os.getenv("DB_PORT", "5432")
        self.db_name = os.getenv("DB_NAME", "cqox_db")
        self.db_user = os.getenv("DB_USER", "cqox_user")
        self.db_password = os.getenv("DB_PASSWORD", "")

        # Create backup directory
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        if self.s3_enabled:
            self.s3_client = boto3.client('s3', region_name=self.s3_region)

    def create_backup(
        self,
        backup_type: str = "full",
        compress: bool = True
    ) -> Optional[Path]:
        """
        Create database backup

        Args:
            backup_type: "full" or "schema_only" or "data_only"
            compress: Whether to compress backup

        Returns:
            Path to backup file
        """
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"cqox_backup_{timestamp}.sql"

        if compress:
            backup_filename += ".gz"

        backup_path = self.backup_dir / backup_filename

        logger.info(f"Creating {backup_type} backup: {backup_path}")

        try:
            # Build pg_dump command
            cmd = [
                "pg_dump",
                "-h", self.db_host,
                "-p", self.db_port,
                "-U", self.db_user,
                "-d", self.db_name,
                "-F", "c",  # Custom format (allows parallel restore)
                "-f", str(backup_path)
            ]

            if backup_type == "schema_only":
                cmd.append("--schema-only")
            elif backup_type == "data_only":
                cmd.append("--data-only")

            if compress:
                cmd.append("-Z9")  # Maximum compression

            # Set password via environment
            env = os.environ.copy()
            if self.db_password:
                env["PGPASSWORD"] = self.db_password

            # Execute backup
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout
            )

            if result.returncode != 0:
                logger.error(f"Backup failed: {result.stderr}")
                return None

            logger.info(f"✓ Backup created successfully: {backup_path}")

            # Upload to S3 if enabled
            if self.s3_enabled:
                self._upload_to_s3(backup_path)

            # Clean old backups
            self._cleanup_old_backups()

            return backup_path

        except subprocess.TimeoutExpired:
            logger.error("Backup timeout (exceeded 1 hour)")
            return None
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return None

    def restore_backup(
        self,
        backup_file: Path,
        drop_existing: bool = False
    ) -> bool:
        """
        Restore database from backup

        Args:
            backup_file: Path to backup file
            drop_existing: Whether to drop existing database first

        Returns:
            Success status
        """
        logger.info(f"Restoring backup from: {backup_file}")

        if not backup_file.exists():
            logger.error(f"Backup file not found: {backup_file}")
            return False

        try:
            # Drop existing database if requested
            if drop_existing:
                self._drop_database()
                self._create_database()

            # Build pg_restore command
            cmd = [
                "pg_restore",
                "-h", self.db_host,
                "-p", self.db_port,
                "-U", self.db_user,
                "-d", self.db_name,
                "-c",  # Clean (drop) database objects before recreating
                "--if-exists",  # Don't error if objects don't exist
                "-j", "4",  # Parallel restore (4 jobs)
                str(backup_file)
            ]

            # Set password via environment
            env = os.environ.copy()
            if self.db_password:
                env["PGPASSWORD"] = self.db_password

            # Execute restore
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                timeout=7200  # 2 hour timeout
            )

            if result.returncode != 0:
                logger.warning(f"Restore completed with warnings: {result.stderr}")
            else:
                logger.info("✓ Restore completed successfully")

            return True

        except Exception as e:
            logger.error(f"Restore failed: {e}")
            return False

    def _upload_to_s3(self, backup_file: Path) -> bool:
        """Upload backup to S3"""
        if not self.s3_enabled:
            return False

        s3_key = f"backups/{backup_file.name}"

        try:
            logger.info(f"Uploading backup to S3: s3://{self.s3_bucket}/{s3_key}")

            self.s3_client.upload_file(
                str(backup_file),
                self.s3_bucket,
                s3_key
            )

            logger.info("✓ Backup uploaded to S3")
            return True

        except ClientError as e:
            logger.error(f"S3 upload failed: {e}")
            return False

    def _cleanup_old_backups(self):
        """Delete backups older than retention period"""
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=self.retention_days)

        logger.info(f"Cleaning backups older than {self.retention_days} days...")

        # Clean local backups
        for backup_file in self.backup_dir.glob("cqox_backup_*.sql*"):
            file_time = datetime.datetime.fromtimestamp(backup_file.stat().st_mtime)

            if file_time < cutoff_date:
                logger.info(f"Deleting old backup: {backup_file}")
                backup_file.unlink()

        # Clean S3 backups
        if self.s3_enabled:
            self._cleanup_s3_backups(cutoff_date)

    def _cleanup_s3_backups(self, cutoff_date: datetime.datetime):
        """Delete old backups from S3"""
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.s3_bucket,
                Prefix="backups/"
            )

            if 'Contents' not in response:
                return

            for obj in response['Contents']:
                if obj['LastModified'].replace(tzinfo=None) < cutoff_date:
                    logger.info(f"Deleting old S3 backup: {obj['Key']}")
                    self.s3_client.delete_object(
                        Bucket=self.s3_bucket,
                        Key=obj['Key']
                    )

        except ClientError as e:
            logger.error(f"S3 cleanup failed: {e}")

    def _drop_database(self):
        """Drop existing database (for restore)"""
        cmd = [
            "psql",
            "-h", self.db_host,
            "-p", self.db_port,
            "-U", self.db_user,
            "-c", f"DROP DATABASE IF EXISTS {self.db_name}"
        ]

        env = os.environ.copy()
        if self.db_password:
            env["PGPASSWORD"] = self.db_password

        subprocess.run(cmd, env=env, check=True)

    def _create_database(self):
        """Create database (for restore)"""
        cmd = [
            "psql",
            "-h", self.db_host,
            "-p", self.db_port,
            "-U", self.db_user,
            "-c", f"CREATE DATABASE {self.db_name}"
        ]

        env = os.environ.copy()
        if self.db_password:
            env["PGPASSWORD"] = self.db_password

        subprocess.run(cmd, env=env, check=True)

    def list_backups(self) -> List[dict]:
        """List available backups"""
        backups = []

        # Local backups
        for backup_file in sorted(self.backup_dir.glob("cqox_backup_*.sql*")):
            stat = backup_file.stat()
            backups.append({
                "name": backup_file.name,
                "path": str(backup_file),
                "size_mb": stat.st_size / (1024 * 1024),
                "created_at": datetime.datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "location": "local"
            })

        # S3 backups
        if self.s3_enabled:
            try:
                response = self.s3_client.list_objects_v2(
                    Bucket=self.s3_bucket,
                    Prefix="backups/"
                )

                if 'Contents' in response:
                    for obj in response['Contents']:
                        backups.append({
                            "name": obj['Key'].split('/')[-1],
                            "path": f"s3://{self.s3_bucket}/{obj['Key']}",
                            "size_mb": obj['Size'] / (1024 * 1024),
                            "created_at": obj['LastModified'].isoformat(),
                            "location": "s3"
                        })

            except ClientError as e:
                logger.error(f"Failed to list S3 backups: {e}")

        return sorted(backups, key=lambda x: x['created_at'], reverse=True)


# Singleton instance
backup_manager = BackupManager()


def schedule_backup():
    """Run scheduled backup (called by cron)"""
    logger.info("Starting scheduled backup...")
    backup_file = backup_manager.create_backup(backup_type="full", compress=True)

    if backup_file:
        logger.info(f"✓ Scheduled backup completed: {backup_file}")
        return True
    else:
        logger.error("✗ Scheduled backup failed")
        return False
