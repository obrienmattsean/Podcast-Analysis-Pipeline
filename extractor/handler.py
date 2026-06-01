"""Local runner for extract-transform-load pipeline smoke checks."""

import logging
import os
from pprint import pprint

from dotenv import load_dotenv
from extract import (
    extract_new_episodes,
    insert_podcast,
)
from load import load_all_episodes
from transform import transform_all_podcast_episodes
from utils import get_database_connection, get_s3_client

# Configure logging to file and console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger()
load_dotenv()
BUCKET_NAME: str = os.environ["S3_BUCKET_NAME"]


def lambda_handler(event=None, context=None):
    """Main Lambda handler function for the podcast episode ETL pipeline.

    This function orchestrates the entire extract-transform-load process for
    podcast episodes. It is designed to be triggered by an AWS Lambda event.

    Args:
        event: The event data that triggered the Lambda function.
        context: The runtime information of the Lambda function.
    Returns:
        dict: A response dictionary with status code and message.
    """

    logger.info("Starting daily episode pipeline")

    db_conn = None
    s3_client = None

    try:
        # Step 1: Extract new episodes from RSS feeds
        logger.info("Step 1: Extracting episodes from RSS feeds")
        db_conn = get_database_connection()
        s3_client = get_s3_client()

        if event is not None and "rss_url" in event:
            logger.info("Received event: %s", event)
            insert_podcast(db_conn, event["rss_url"])

        extracted_data = extract_new_episodes(db_conn)
        logger.info("Successfully extracted episodes for %s podcasts", len(extracted_data))

        # Step 2: Transform and validate episode data
        logger.info("Step 2: Transforming and validating episode data")
        transformed_data = transform_all_podcast_episodes(extracted_data)
        logger.info(
            "Successfully transformed %s podcasts with validated episodes",
            len(transformed_data),
        )

        # Step 3: Load validated episodes into database
        logger.info("Step 3: Loading episodes into RDS database")
        uploaded_paths = load_all_episodes(db_conn, s3_client, transformed_data, BUCKET_NAME)

        # Return success response with a list of uploaded S3 paths
        response_body = {
            "statusCode": 200,
            "message": "Daily episode pipeline completed successfully",
            "uploaded_paths": uploaded_paths,
        }
        logger.info("Pipeline completed successfully")
        return response_body
    finally:
        if db_conn is not None:
            db_conn.close()
        if s3_client is not None:
            s3_client.close()


if __name__ == "__main__":
    # Run the Lambda handler locally for testing
    url = "https://media.rss.com/waitdontdoit/feed.xml"
    a = lambda_handler({"rss_url": url}, None)
    pprint(a)
