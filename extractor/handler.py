"""Local runner for extract-transform-load pipeline smoke checks."""

import json
import logging
from pprint import pprint

from extract import (
  extract_new_episodes,
  get_database_connection,
  get_episodes_from_rss,
  insert_podcast,
)
from load import get_s3_client, get_staged_episodes_for_podcast, load_all_episodes
from transform import transform_all_podcast_episodes

logger = logging.getLogger()
logger.setLevel(logging.INFO)


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
    insert_podcast(event["rss_url"])

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
  logger.info("Successfully transformed %s podcasts with validated episodes", len(transformed_data))

  # Step 3: Load validated episodes into database
  logger.info("Step 3: Loading episodes into RDS database")
  load_all_episodes(db_conn, s3_client, transformed_data)
  # Close database connection
  db_conn.close()
  s3_client.close()

  # Return success response with detailed statistics
  response_body = {
    "status": "success",
    "message": "Daily episode pipeline completed successfully",
  }
  logger.info("Pipeline completed successfully")
  return {"statusCode": 200, "body": json.dumps(response_body)}


if __name__ == "__main__":
  url = "https://media.rss.com/fluxcapacitor/feed.xml"
  curr, after = get_episodes_from_rss(url)[:2]

  mock = {
    "podcast_id": 1,
    "podcast_title": "Flux Capacitor",
    "rss_url": url,
    "new_episodes": [curr, after],
  }
  transformed = transform_all_podcast_episodes([mock])
  load_all_episodes(transformed)

  res = get_staged_episodes_for_podcast(
    get_s3_client(), {"id": 1, "title": "Flux Capacitor", "rss_url": url}
  )
  pprint(res)
