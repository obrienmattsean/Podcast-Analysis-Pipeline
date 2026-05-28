import logging
import os

import boto3
from psycopg2 import connect
from psycopg2.extensions import connection

logger = logging.getLogger(__name__)


def get_database_connection() -> connection:
    """Create a PostgreSQL connection from environment configuration.

    Returns:
        connection: Active psycopg2 database connection.

    Raises:
        Exception: Raised when the database connection fails.
    """

    try:
        return connect(
            host=os.getenv("RDS_HOST"),
            database=os.getenv("RDS_DBNAME"),
            user=os.getenv("RDS_USER"),
            password=os.getenv("RDS_PASSWORD"),
        )
    except Exception:
        logger.exception("Failed to connect to database")
        raise


def get_s3_client():
    """Initialize an S3 client using AWS environment credentials.

    Returns:
        botocore.client.BaseClient: Configured S3 client.

    Raises:
        Exception: Raised when client initialization fails.
    """

    try:
        return boto3.client(
            "s3",
            region_name=os.getenv("AWS_REGION", "eu-west-2"),
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        )
    except Exception:
        logger.exception("Failed to initialize S3 client")
        raise
