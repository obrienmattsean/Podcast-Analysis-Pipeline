"""Python module to load validated episodes to S3 as JSON."""

import json
import logging
import os
from datetime import datetime

import boto3
from model import ValidatedEpisode
from psycopg2 import connect
from psycopg2.extensions import connection

BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "c23-podex-ai-bucket")


logger = logging.getLogger(__name__)


def get_database_connection():
  """Create a PostgreSQL connection from environment configuration.

  Returns:
      connection: Active psycopg2 database connection.

  Raises:
      Exception: Raised when the database connection fails.
  """

  try:
    return connect(
      host=os.getenv("RDS_HOST"),
      database=os.getenv("RDS_DB_NAME"),
      user=os.getenv("RDS_USERNAME"),
      password=os.getenv("RDS_PASSWORD"),
    )
  except Exception:
    logger.exception("Failed to connect to database")
    raise


def get_s3_client():
  """Initialize an S3 client using AWS environment credentials.

  Returns:
      botocore.client.BaseClient: Configured S3 client.

  Raises:
      Exception: Raised when client initialization fails.
  """

  try:
    return boto3.client(
      "s3",
      region_name=os.getenv("AWS_REGION", "eu-west-2"),
      aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
      aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    )
  except Exception:
    logger.exception("Failed to initialize S3 client")
    raise


def serialize_episode(episode: ValidatedEpisode) -> dict:
  """Serialize a validated episode into a JSON-friendly dictionary.

  Args:
      episode (ValidatedEpisode): Validated episode model.

  Returns:
      dict: Serialized episode payload.
  """

  episode_dict = episode.model_dump()
  if isinstance(episode_dict.get("published_at"), datetime):
    episode_dict["published_at"] = episode_dict["published_at"].isoformat()
  if episode_dict.get("audio_link"):
    episode_dict["audio_link"] = str(episode_dict["audio_link"])
  return episode_dict


def _insert_episodes_to_db(conn, episodes: list[dict]) -> list[dict]:
  """
  Insert episodes and return enriched payloads safely.
  Each result keeps its own episode_id (or None if failed).

  Args:
      episodes (list[dict]): List of serialized episode payloads.

  Returns:
      list[dict]: Enriched episode payloads with episode_id fields.
  """

  results = []
  if not episodes:
    return []

  with conn.cursor() as cursor:
    for episode in episodes:
      try:
        cursor.execute(
          """
                    INSERT INTO episodes (podcast_id, title, audio_url, published_at)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                    """,
          (
            episode.get("podcast_id"),
            episode.get("title"),
            episode.get("audio_link"),
            episode.get("published_at"),
          ),
        )

        episode_id = cursor.fetchone()[0]
        episode["episode_id"] = episode_id
        results.append(episode)
        conn.commit()

      except Exception as e:
        logger.warning(
          "Failed insert for episode=%s error=%s",
          episode.get("title"),
          str(e),
        )
        episode["episode_id"] = None
        conn.rollback()

  return results


def build_episode_list_payload(conn, podcast_episode_data: dict) -> list[dict]:
  """Insert episodes and return enriched payload.

  Args:
      conn: Active psycopg2 database connection.
      podcast_episode_data (dict): Podcast episode data dictionary with structure:
                                 {
                                     'podcast_id': int,
                                     'podcast_title': str,
                                     'new_episodes': list[ValidatedEpisode]
                                 }
  Returns:
      list[dict]: List of enriched episode payloads with episode_id fields.
  """

  episodes = podcast_episode_data.get("new_episodes", [])
  if not episodes:
    return []

  serialized = [serialize_episode(ep) for ep in episodes]
  enriched = _insert_episodes_to_db(conn, serialized)

  return enriched


def upload_podcast_payload_to_s3(
  s3_client, bucket: str, podcast_id: int, episodes_payload: list[dict]
) -> None:
  """Upload a single JSON array file for one podcast to S3.

  Args:
      s3_client: Configured S3 client.
      bucket (str): Target S3 bucket name.
      podcast_id (int): Podcast identifier.
      episodes_payload (list[dict]): Episode payloads to upload.

  Raises:
      Exception: Raised when the S3 upload fails.
  """

  if not episodes_payload:
    return

  s3_key = f"podcasts/staging/{podcast_id}/episodes.json"
  json_content = json.dumps(episodes_payload, indent=2)

  s3_client.put_object(
    Bucket=bucket,
    Key=s3_key,
    Body=json_content,
    ContentType="application/json",
  )
  logger.info("Uploaded %d episodes to s3://%s/%s", len(episodes_payload), bucket, s3_key)


def load_podcast_episodes(
  conn: connection, s3_client, bucket: str, podcast_episode_data: dict
) -> tuple[int, int]:
  """Load one podcast's episodes to DB and S3.

  Args:
      conn: Active psycopg2 database connection.
      s3_client: Configured S3 client.
      bucket (str): Target S3 bucket name.
      podcast_episode_data (dict): Podcast payload with new episodes.

  Returns:
      tuple[int, int]: Counts in the form (uploaded, failed).
  """

  podcast_id = podcast_episode_data.get("podcast_id")
  episodes = podcast_episode_data.get("new_episodes", [])

  if not episodes:
    return 0, 0

  try:
    episodes_payload = build_episode_list_payload(conn, podcast_episode_data)
    upload_podcast_payload_to_s3(s3_client, bucket, podcast_id, episodes_payload)
    return len(episodes_payload), len(episodes) - len(episodes_payload)
  except Exception:
    logger.exception("Failed to load podcast episodes for id=%s", podcast_id)
    return 0, len(episodes)


def load_all_episodes(
  conn: connection, s3_client, podcast_episodes_list: list, bucket: str = BUCKET_NAME
) -> None:
  """Loads episodes for all podcasts into the database

  Main orchestration function that loads validated episodes from all podcasts
  into the RDS database.

  Args:
      conn: PostgreSQL database connection object
      podcast_episodes_list: List of podcast data dictionaries with structure:
                             [
                                 {
                                     'podcast_id': int,
                                     'podcast_name': str,
                                     'new_episodes': list[dict]
                                 },
                                 ...
                             ]
  """
  total_uploaded = 0
  total_failed = 0

  for podcast_episode_data in podcast_episodes_list:
    uploaded_count, failed_count = load_podcast_episodes(
      conn,
      s3_client,
      bucket,
      podcast_episode_data,
    )
    total_uploaded += uploaded_count
    total_failed += failed_count

  logger.info("Episode load complete. uploaded=%d failed=%d", total_uploaded, total_failed)
