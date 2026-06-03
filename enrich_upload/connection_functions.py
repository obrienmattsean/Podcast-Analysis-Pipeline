"""Connection functions for the Podcast Analysis Pipeline.

This module creates all the connection functions for the Podcast Analysis Pipeline
for reference in the completed script. Connections are established by requesting the
OpenAI API, AWS S3, and PostgreSQL database to generate
the desired enrichment of podcast transcripts.

Example:
    Typical usage example:

        from enrich_upload.connection_functions import some_function
        connection = some_function(input_data)

"""

import logging

import boto3
import openai as oa
from botocore.client import BaseClient
from dotenv import load_dotenv
from psycopg2 import connect
from psycopg2.extensions import connection as Connection

load_dotenv()


def get_llm_client(openai_api_key: str) -> oa.OpenAI:
    """Creates the OpenAI client to make requests to the OpenAI API.

    Args:
        openai_api_key (str): The OpenAI API key.

    Returns:
        oa.OpenAI: The initialized OpenAI client.

    Raises:
        TypeError: If the API key is missing or not a string.
        ValueError: If the API key is an empty string.
        Exception: If there is an error initializing the OpenAI client.

    """
    logging.info("Initializing OpenAI client.")
    try:
        if not isinstance(openai_api_key, str):
            raise TypeError("API key is required to initialize OpenAI client")
        if not openai_api_key:
            raise ValueError("API key cannot be empty to initialize OpenAI client")
        client = oa.OpenAI(api_key=openai_api_key)
        logging.info("OpenAI client initialized successfully.")
        return client
    except Exception as e:
        logging.error(f"Failed to initialize OpenAI client: {e}")
        raise


def get_s3_client(
    region_name: str,
    aws_access_key_id: str | None = None,
    aws_secret_access_key: str | None = None,
) -> BaseClient:
    """Creates the S3 client to interact with AWS S3.

    When running in AWS Lambda, credentials are provided automatically via the
    IAM execution role, so aws_access_key_id and aws_secret_access_key can be omitted.
    For local testing, provide explicit credentials or use ~/.aws/credentials.

    Args:
        region_name(str): The AWS region name (required).
        aws_access_key_id(str, optional): The AWS access key ID. If not provided,
            boto3 will use IAM role credentials (Lambda) or ~/.aws/credentials.
        aws_secret_access_key(str, optional): The AWS secret access key. If not provided,
            boto3 will use IAM role credentials (Lambda) or ~/.aws/credentials.

    Returns:
        BaseClient: The initialized S3 client.

    Raises:
        TypeError: If region_name is not a string.
        ValueError: If region_name is empty.
        Exception: If there is an error initializing the S3 client.

    """
    logging.info("Initializing S3 client.")

    if not isinstance(region_name, str):
        raise TypeError("Region name is required as a string to initialize S3 client")

    if not region_name:
        raise ValueError("Region name cannot be empty")

    try:
        # Build kwargs only with provided credentials
        client_kwargs = {"region_name": region_name}
        if aws_access_key_id is not None and aws_secret_access_key is not None:
            client_kwargs["aws_access_key_id"] = aws_access_key_id
            client_kwargs["aws_secret_access_key"] = aws_secret_access_key

        s3_client = boto3.client("s3", **client_kwargs)
        logging.info("S3 client initialized successfully.")
        return s3_client
    except Exception as e:
        logging.error(f"Failed to initialize S3 client: {e}")
        raise


def get_db_connection(host: str, database: str, user: str, password: str, port: str) -> Connection:
    """Creates the connection to interact with the RDS hosted on AWS.

    Args:
        host (str): The database host.
        database (str): The database name.
        user (str): The database user.
        password (str): The database password.
        port (str): The database port.


    Returns:
        Connection: A connection object to the PostgreSQL database
        specified by environment variables.

    Raises:
        ValueError: If any of the required environment variables are empty.
        TypeError: If any of the required environment variables are not strings.
        Exception: If there is an error connecting to the database, an exception will be raised with
        the error message.

    """
    try:
        if not host or not port or not database or not user or not password:
            raise ValueError("Database connection parameters are missing in environment variables")
        if not all(isinstance(param, str) for param in [host, port, database, user, password]):
            raise TypeError(
                "Database connection parameters must be strings in environment variables"
            )
        connection = connect(host=host, port=port, database=database, user=user, password=password)
        logging.info("Database connection established successfully.")
        return connection
    except Exception as e:
        logging.error(f"Failed to connect to the database: {e}")
        raise
