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
import os

import boto3
import openai as oa
from botocore.client import BaseClient
from dotenv import load_dotenv
from psycopg2 import Connection, connect

logger = logging.getLogger(__name__)

load_dotenv()  # Load environment variables from .env file


def get_llm_client() -> oa.OpenAI:
    """Creates the OpenAI client to make requests to the OpenAI API.

    Args:
        None: no arguments are required for this function.
        But environment variables are used within the function.


    Returns:
        oa.OpenAI: The initialized OpenAI client.

    Raises:
        TypeError: If the API key is missing or not a string.
        ValueError: If the API key is an empty string.
        Exception: If there is an error initializing the OpenAI client.

    """
    logger.info("Initializing OpenAI client.")
    try:
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not isinstance(openai_api_key, str):
            raise TypeError("API key is required to initialize OpenAI client")
        if not openai_api_key:
            raise ValueError("API key cannot be empty to initialize OpenAI client")
        client = oa.OpenAI(api_key=openai_api_key)
        logger.info("OpenAI client initialized successfully.")
        return client
    except Exception as e:
        logger.error(f"Failed to initialize OpenAI client: {e}")
        raise


def get_s3_client(
    aws_access_key_id: str, aws_secret_access_key: str, region_name: str
) -> BaseClient:
    """Creates the S3 client to interact with AWS S3.

    Args:
        aws_access_key_id(str): The AWS access key ID. This should be stored
        as an environment variable and passed to the function.
        aws_secret_access_key(str): The AWS secret access key. This should be stored
        as an environment variable and passed to the function.
        region_name(str): The AWS region name. This should be stored
        as an environment variable and passed to the function.

    Returns:
        client: The initialized S3 client.

    Raises:
        TypeError: If any of the required parameters are not strings.
        ValueError: If any of the required parameters are empty.
        Exception: If there is an error initializing the S3 client.

    """

    if (
        not isinstance(aws_access_key_id, str)
        or not isinstance(aws_secret_access_key, str)
        or not isinstance(region_name, str)
    ):
        raise TypeError(
            """AWS access key ID, secret access key, and region name are
                    required as strings to initialize S3 client"""
        )
        logger.info("Initializing S3 client.")

    if not aws_access_key_id or not aws_secret_access_key or not region_name:
        raise ValueError("AWS access key ID, secret access key, and region name cannot be empty")
    try:
        s3_client = boto3.client(
            "s3",
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name,
        )
        logger.info("S3 client initialized successfully.")
        return s3_client
    except Exception as e:
        logger.error(f"Failed to initialize S3 client: {e}")
        raise


def get_db_connection() -> Connection:
    """Creates the connection to interact with the RDS hosted on AWS.

    Args:
        None: no arguments are required for this function.
        But environment variables are used withing the function.

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
        host = os.getenv("DB_HOST")
        port = os.getenv("DB_PORT")
        database = os.getenv("DB_NAME")
        user = os.getenv("DB_USER")
        password = os.getenv("DB_PASSWORD")
        if not host or not port or not database or not user or not password:
            raise ValueError("Database connection parameters are missing in environment variables")
        if not all(isinstance(param, str) for param in [host, port, database, user, password]):
            raise TypeError(
                "Database connection parameters must be strings in environment variables"
            )
        connection = connect(host=host, port=port, database=database, user=user, password=password)
        logger.info("Database connection established successfully.")
        return connection
    except Exception as e:
        logger.error(f"Failed to connect to the database: {e}")
        raise
