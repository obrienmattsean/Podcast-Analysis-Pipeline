import json
import logging
import os

import boto3
from psycopg2 import connect
from psycopg2.extensions import connection


def get_secrets() -> dict:
    client = boto3.client("secretsmanager")

    resp = client.get_secret_value(SecretId=os.environ["SECRETS_ARN"])

    return json.loads(resp["SecretString"])


def get_database_connection() -> connection:
    """Create a PostgreSQL connection from environment configuration.

    Returns:
        connection: Active psycopg2 database connection.

    Raises:
        Exception: Raised when the database connection fails.
    """

    try:
        secrets = get_secrets()

        return connect(
            host=secrets["RDS_HOST"],
            database=secrets["RDS_DBNAME"],
            user=secrets["RDS_USER"],
            password=secrets["RDS_PASSWORD"],
            port=5432,
            sslmode="require",
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
