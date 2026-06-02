"""Python module to load validated episodes to S3 as JSON."""

import json
import logging
from datetime import datetime

from botocore.client import BaseClient
from model import ValidatedEpisode
from psycopg2.extensions import connection

logger = logging.getLogger(__name__)


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


def _insert_episodes_to_db(conn: connection, episodes: list[dict]) -> list[dict]:
    """
    Insert episodes and return enriched payloads safely.
    Each result keeps its own episode_id (or None if failed).

    Args:
        conn: Active psycopg2 database connection.
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
                    INSERT INTO episodes (podcast_id, title, audio_url, pub_date)
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

                result = cursor.fetchone()
                episode["episode_id"] = result[0] if result else None
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


def build_episode_list_payload(conn: connection, podcast_episode_data: dict) -> list[dict]:
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


def upload_episode_to_s3(
    s3_client: BaseClient, bucket: str, podcast_id: int, episode: dict
) -> str | None:
    """Upload a single episode metadata to S3.

    Args:
        s3_client: Configured S3 client.
        bucket (str): Target S3 bucket name.
        podcast_id (int): Podcast identifier.
        episode (dict): Episode payload to upload.

    Returns:
        str | None: Uploaded object path in S3, or None if episode is missing an id.
    """

    if not episode or not episode.get("episode_id"):
        return None

    episode_id = episode["episode_id"]
    s3_key = f"{podcast_id}/{episode_id}"
    json_content = json.dumps(episode, indent=2)

    s3_client.put_object(
        Bucket=bucket,
        Key=s3_key + "/metadata.json",
        Body=json_content,
        ContentType="application/json",
    )
    logger.info("Uploaded episode to s3://%s/%s", bucket, s3_key)
    return f"s3://{bucket}/{s3_key}/"


def upload_podcast_payload_to_s3(
    s3_client: BaseClient, bucket: str, podcast_id: int, episodes_payload: list[dict]
) -> list[str]:
    """Upload episodes to S3 as individual metadata files.

    Args:
        s3_client: Configured S3 client.
        bucket (str): Target S3 bucket name.
        podcast_id (int): Podcast identifier.
        episodes_payload (list[dict]): Episode payloads to upload.

    Returns:
        list[str]: Paths for uploaded episode metadata objects.
    """

    if not episodes_payload:
        return []

    uploaded_paths = []

    for episode in episodes_payload:
        try:
            path = upload_episode_to_s3(s3_client, bucket, podcast_id, episode)
            if path:
                uploaded_paths.append(path)
        except Exception:
            logger.exception(
                "Failed to upload episode id=%s for podcast id=%s",
                episode.get("episode_id"),
                podcast_id,
            )

    logger.info("Uploaded %d episodes for podcast id=%s", len(uploaded_paths), podcast_id)
    return uploaded_paths


def load_podcast_episodes(
    conn: connection, s3_client: BaseClient, bucket: str, podcast_episode_data: dict
) -> tuple[int, int, list[str]]:
    """Load one podcast's episodes to DB and S3.

    Args:
        conn: Active psycopg2 database connection.
        s3_client: Configured S3 client.
        bucket (str): Target S3 bucket name.
        podcast_episode_data (dict): Podcast payload with new episodes.

    Returns:
        tuple[int, int, list[str]]: Counts in the form (uploaded, failed)
        and uploaded S3 paths.
    """

    podcast_id = podcast_episode_data.get("podcast_id")
    episodes = podcast_episode_data.get("new_episodes", [])

    if not episodes:
        return 0, 0, []

    if not isinstance(podcast_id, int):
        logger.warning("Missing or invalid podcast_id=%s, skipping load", podcast_id)
        return 0, len(episodes), []

    try:
        episodes_payload = build_episode_list_payload(conn, podcast_episode_data)
        uploaded_paths = upload_podcast_payload_to_s3(
            s3_client, bucket, podcast_id, episodes_payload
        )
        return len(episodes_payload), len(episodes) - len(episodes_payload), uploaded_paths
    except Exception:
        logger.exception("Failed to load podcast episodes for id=%s", podcast_id)
        return 0, len(episodes), []


def load_all_episodes(
    conn: connection, s3_client: BaseClient, podcast_episodes_list: list, bucket: str
) -> list[str]:
    """Loads episodes for all podcasts into the database and S3.

    Main orchestration function that loads validated episodes from all podcasts
    into the RDS database and S3.

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
        bucket: Target S3 bucket name
    Returns:
        list: List of uploaded S3 paths for all episodes.
    """
    total_uploaded = 0
    total_failed = 0
    all_uploaded_paths = []

    for podcast_episode_data in podcast_episodes_list:
        uploaded_count, failed_count, uploaded_paths = load_podcast_episodes(
            conn,
            s3_client,
            bucket,
            podcast_episode_data,
        )
        total_uploaded += uploaded_count
        total_failed += failed_count
        all_uploaded_paths.extend(uploaded_paths)

    logger.info("Episode load complete. uploaded=%d failed=%d", total_uploaded, total_failed)
    return all_uploaded_paths
