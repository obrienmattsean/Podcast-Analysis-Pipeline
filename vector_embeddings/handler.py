"""Lambda handler for podcast transcript embedding pipeline.

Orchestrates the ETL (Extract, Transform, Load) process for converting
podcast transcripts to vector embeddings and storing them in the database.
"""

import logging

from botocore.exceptions import ClientError
from extract import extract_episode_id, fetch_transcript_from_s3, get_s3_client
from load import get_db_connection, insert_embeddings
from openai import OpenAIError
from transform import get_openai_client, process_transcript

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def lambda_handler(event: dict, context: dict = None) -> dict:
    """Process podcast transcript and store vector embeddings in database.

    Implements the ETL pipeline:
    - Extract: Retrieve transcript from S3
    - Transform: Generate embeddings for transcript chunks
    - Load: Insert embeddings into RDS database

    Args:
        event: Lambda event containing upload_path (S3 URI of transcript).
        context: Lambda context object (unused, provided by AWS
            Lambda runtime).

    Returns:
        Response dict with statusCode and body message.
        - 200: Embeddings successfully inserted.
        - 400: Missing required upload_path parameter.

    Raises:
        ClientError: If S3 transcript retrieval fails.
        OpenAIError: If embedding generation fails.
        Exception: If any unexpected processing error occurs.

    Example:
        >>> event = {"upload_path": "s3://bucket/26/199/"}
        >>> response = lambda_handler(event)
        >>> response["statusCode"]
        200
    """
    logger.info("Received event: %s", event)
    upload_path = event.get("upload_path")
    if not upload_path:
        return {"statusCode": 400, "body": "Missing upload_path in event"}

    s3_client = None
    openai_client = None
    conn = None

    try:
        s3_client = get_s3_client()
        openai_client = get_openai_client()
        conn = get_db_connection()

        logger.info("EXTRACT: Fetching transcript from S3...")
        transcript = fetch_transcript_from_s3(s3_client, upload_path)
        episode_id = extract_episode_id(upload_path)

        logger.info("TRANSFORM: Processing transcript...")
        embedded_chunks = process_transcript(openai_client, transcript)

        logger.info("LOAD: Inserting embeddings into database...")
        insert_embeddings(conn, episode_id, embedded_chunks)

        return {"statusCode": 200, "body": "Embeddings inserted successfully"}

    except ClientError as e:
        logger.error("Error occurred when fetching transcript from S3: %s", str(e))
        raise

    except OpenAIError as e:
        logger.error("Error occurred when generating embeddings: %s", str(e))
        raise

    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise

    finally:
        if s3_client is not None:
            s3_client.close()
        if openai_client is not None:
            openai_client.close()
        if conn is not None:
            conn.close()


if __name__ == "__main__":
    # For local testing
    event = {"upload_path": "s3://c23-podex-ai-bucket/26/199/"}
    response = lambda_handler(event)
    print(response)
