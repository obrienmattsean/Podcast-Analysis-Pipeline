"""The enrichment_upload_handler module serves as the main script for handling this section of
the pipeline within an AWS Lambda function.


the enrichment upload process in the Podcast Analysis Pipeline. It orchestrates the retrieval
of podcast transcripts and metadata from S3, generates enrichments using the OpenAI API, and
uploads the enriched data to an RDS database. The module ensures that all connections are properly
established and that errors are handled gracefully throughout the process.

"""

import json
import logging

import boto3
from connection_functions import get_db_connection, get_llm_client, get_s3_client
from dotenv import load_dotenv
from enrichment_functions import (
    get_episode_metadata_from_s3,
    get_episode_transcript_from_s3,
    prompt_llm_for_enrichment,
)
from upload_functions import combine_enrichments, upload_to_rds

logger = logging.getLogger()
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger.setLevel(logging.INFO)


def get_secrets() -> dict:
    """Retrieves secrets from AWS Secrets Manager.

    Returns:
        dict: A dictionary containing the retrieved secrets.

    Raises:
        json.JSONDecodeError: If the secret string is not valid JSON.
        Exception: If retrieval fails.
    """
    secrets_client = boto3.client("secretsmanager", region_name="eu-west-2")
    try:
        logger.info("Retrieving secrets from AWS Secrets Manager...")
        response = secrets_client.get_secret_value(SecretId="c23-podex-ai-app-secrets")
        secret_string = response["SecretString"]
        secrets = json.loads(secret_string)
        logger.info("Secrets retrieved and parsed successfully.")
        return secrets
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse secret as JSON: {e}")
        raise ValueError(f"Secret is not valid JSON: {e}") from e
    except Exception as e:
        logger.error(f"Failed to retrieve secrets from Secrets Manager: {e}")
        raise


load_dotenv()


def lambda_handler(event, context):
    """AWS Lambda handler function to process podcast enrichment uploads.

    This function is triggered by an event (e.g., S3 upload) and performs the following steps:
    1. Retrieves the episode transcript and metadata from S3.
    2. Generates enrichments using the OpenAI API.
    3. Combines the enrichments with the episode metadata.
    4. Uploads the combined data to an RDS database.

    Args:
        event (dict): The event data that triggered the Lambda function.
        context (object): The context in which the Lambda function is running.

    Returns:
        dict: A response indicating the success or failure of the operation.

    """
    logger.info("Lambda function started with event")
    if "episode_uri" not in event:
        logger.error("Missing 'episode_uri' in event data.")
        raise ValueError("Missing 'episode_uri' in event data.")

    db_connection = None

    # Step 1: Retrieve secrets from Secrets Manager
    logger.info("Retrieving secrets for database and API connections.")
    secrets = get_secrets()

    # Validate all required secrets are present
    required_keys = [
        "OPENAI_API_KEY",
        "RDS_HOST",
        "RDS_DBNAME",
        "RDS_USER",
        "RDS_PASSWORD",
        "RDS_PORT",
    ]
    missing_keys = [key for key in required_keys if key not in secrets or not secrets.get(key)]
    if missing_keys:
        raise ValueError(f"Missing required secrets in Secrets Manager: {', '.join(missing_keys)}")

    logger.info("Establishing connections to OpenAI, S3, and RDS.")
    llm_client = get_llm_client(secrets["OPENAI_API_KEY"])
    # S3 client uses IAM role in Lambda, no credentials needed
    s3_client = get_s3_client("eu-west-2")
    db_connection = get_db_connection(
        secrets["RDS_HOST"],
        secrets["RDS_DBNAME"],
        secrets["RDS_USER"],
        secrets["RDS_PASSWORD"],
        secrets["RDS_PORT"],
    )
    logger.info("Connections established successfully.")

    metadata = get_episode_metadata_from_s3(s3_client, event["episode_uri"])
    transcript = get_episode_transcript_from_s3(s3_client, event["episode_uri"])
    logger.info("Episode transcript and metadata retrieved successfully.")
    logger.info("Prompting LLM for enrichment with transcript")
    enrichment_data = prompt_llm_for_enrichment(llm_client, transcript)
    logger.info("Enrichment data received from LLM.")

    # Step 3: Combine enrichments with episode metadata and moderation
    combined_data = combine_enrichments(metadata, enrichment_data)
    logger.info("Combining enrichments with episode metadata for upload.")
    upload_to_rds(combined_data, db_connection)
    logger.info("Enrichment data uploaded successfully to RDS.")

    return {
        "statusCode": 200,
        "message": "Enrichment upload successful!",
        "episode_id": metadata.get("episode_id"),
    }
