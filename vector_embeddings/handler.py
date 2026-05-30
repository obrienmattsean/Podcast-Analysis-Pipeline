import logging

from extract import extract_episode_id, fetch_transcript_from_s3, get_s3_client
from load import get_db_connection, insert_embeddings
from transform import process_transcript

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def lambda_handler(event, context=None):
    logger.info("Received event: %s", event)
    upload_path = event.get("upload_path")
    if not upload_path:
        return {"statusCode": 400, "body": "Missing upload_path in event"}
    s3_client = get_s3_client()
    conn = get_db_connection()

    logger.info("EXTRACT: Fetching transcript from S3...")
    transcript = fetch_transcript_from_s3(s3_client, upload_path)
    episode_id = extract_episode_id(upload_path)
    logger.info("TRANSFORM: Processing transcript...")
    embedded_chunks = process_transcript(transcript)
    logger.info("LOAD: Inserting embeddings into database...")
    insert_embeddings(conn, episode_id, embedded_chunks)

    s3_client.close()
    conn.close()

    return {"statusCode": 200, "body": "Embeddings inserted successfully"}


if __name__ == "__main__":
    # For local testing
    event = {"upload_path": "s3://c23-podex-ai-bucket/26/199/"}
    response = lambda_handler(event)
    print(response)
