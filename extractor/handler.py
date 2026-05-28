"""Local runner for extract-transform-load pipeline smoke checks."""

import logging
from pathlib import Path

from dotenv import load_dotenv
from extract import (
    extract_new_episodes,
    insert_podcast,
)
from load import load_all_episodes
from transform import transform_all_podcast_episodes
from utility import get_database_connection, get_s3_client

# Configure logging to file and console
log_dir = Path(__file__).resolve().parents[1] / "logs"
log_dir.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_dir / "podcast_pipeline.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger()


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
    if event is not None:
        print(f"Received event: {event}")
        insert_podcast(event["rss_url"], event.get("title", "unknown"))

    logger.info("Starting daily episode pipeline")

    # Step 1: Extract new episodes from RSS feeds
    logger.info("Step 1: Extracting episodes from RSS feeds")
    db_conn = get_database_connection()
    s3_client = get_s3_client()
    extracted_data = extract_new_episodes(db_conn)
    logger.info("Successfully extracted episodes for %s podcasts", len(extracted_data))

    # Step 2: Transform and validate episode data
    logger.info("Step 2: Transforming and validating episode data")
    transformed_data = transform_all_podcast_episodes(extracted_data)
    logger.info(
        "Successfully transformed %s podcasts with validated episodes", len(transformed_data)
    )

    # Step 3: Load validated episodes into database
    logger.info("Step 3: Loading episodes into RDS database")
    uploaded_paths = load_all_episodes(db_conn, s3_client, transformed_data)
    # Close database connection
    db_conn.close()
    s3_client.close()

    # Return success response with detailed statistics
    response_body = {
        "statusCode": 200,
        "message": "Daily episode pipeline completed successfully",
        "uploaded_paths": uploaded_paths,
    }
    logger.info("Pipeline completed successfully")
    return response_body


if __name__ == "__main__":
    load_dotenv()
    url = "https://media.rss.com/fluxcapacitor/feed.xml"
    lambda_handler({"rss_url": url, "title": "Flux Capacitor"}, None)
