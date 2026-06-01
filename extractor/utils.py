import logging
import os

import boto3
from psycopg2 import connect
from psycopg2.extensions import connection


def get_database_connection() -> connection:
    """Create a PostgreSQL connection from environment configuration.

    Returns:
        connection: Active psycopg2 database connection.

    Raises:
        Exception: Raised when the database connection fails.
    """

    try:
        return connect(
            host=os.getenv(
                "RDS_HOST",
                "c23-podex-ai-podcast-analysis-db.c57vkec7dkkx.eu-west-2.rds.amazonaws.com",
            ),
            database=os.getenv("RDS_DBNAME", "c23_podcast_analysis_db"),
            user=os.getenv("RDS_USER", "postgres"),
            password=os.getenv("RDS_PASSWORD", "Pasword123!"),
            port=int(os.getenv("RDS_PORT", "5432")),
        )
    except Exception:
        logging.exception("Failed to connect to database")
        raise


def get_s3_client():
    """Initialize an S3 client using AWS environment credentials.

    Returns:
        botocore.client.BaseClient: Configured S3 client.

    Raises:
        Exception: Raised when client initialization fails.
    """

    try:
        return boto3.client("s3", region_name=os.getenv("AWS_REGION", "eu-west-2"))
    except Exception:
        logging.exception("Failed to initialize S3 client")
        raise
