"""Python module to load validated episodes to S3 as JSON."""

import json
import logging
import os
from datetime import datetime

import boto3
from model import ValidatedEpisode


def get_logger() -> None:
    """Configures application logging."""

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s [%(name)s] %(message)s"
    )
    return logging.getLogger(__name__)


logger = get_logger()


def get_s3_client():
    """Initialize S3 client using AWS credentials from environment."""

    try:
        logger.info("Initializing S3 client")
        s3_client = boto3.client(
            "s3",
            region_name=os.getenv("AWS_REGION", "eu-west-2"),
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        )
        logger.info("S3 client initialized")
        return s3_client
    except Exception:
        logger.exception("Failed to initialize S3 client")
        raise


def serialize_episode(episode: ValidatedEpisode) -> dict:
    """Convert ValidatedEpisode to a JSON-serializable dict."""

    episode_dict = episode.model_dump()
    # Convert datetime and URL objects to strings
    if isinstance(episode_dict.get("published_at"), datetime):
        episode_dict["published_at"] = episode_dict["published_at"].isoformat()
    if episode_dict.get("audio_link"):
        episode_dict["audio_link"] = str(episode_dict["audio_link"])
    return episode_dict


def upload_episodes_to_s3(
    s3_client, bucket: str, episodes: list[ValidatedEpisode], podcast_id: int
) -> None:
    """Upload a list of ValidatedEpisode objects as JSON to S3."""

    episodes_data = [serialize_episode(episode) for episode in episodes]
    json_content = json.dumps(episodes_data, indent=2)
    s3_key = f"podcasts/{podcast_id}/episodes.json"

    try:
        logger.info(
            "Uploading %d episodes to S3 s3://%s/%s",
            len(episodes),
            bucket,
            s3_key,
        )
        s3_client.put_object(
            Bucket=bucket,
            Key=s3_key,
            Body=json_content,
            ContentType="application/json",
        )
        logger.info(
            "Successfully uploaded %d episodes to s3://%s/%s",
            len(episodes),
            bucket,
            s3_key,
        )
    except Exception:
        logger.exception(
            "Failed to upload episodes to S3. podcast_id=%s s3_key=%s",
            podcast_id,
            s3_key,
        )
        raise


def load_podcast_episodes(
    s3_client, bucket: str, podcast_episode_data: dict
) -> tuple[int, int]:
    """Load episodes for one podcast to S3 and return (uploaded, failed)."""

    podcast_title = podcast_episode_data.get("podcast_title", "unknown")
    podcast_id = podcast_episode_data.get("podcast_id")
    episodes = podcast_episode_data.get("new_episodes", [])

    logger.info(
        "Loading episodes for podcast title=%s id=%s count=%d",
        podcast_title,
        podcast_id,
        len(episodes),
    )

    if not episodes:
        logger.warning("No episodes to load for podcast id=%s", podcast_id)
        return 0, 0

    try:
        upload_episodes_to_s3(s3_client, bucket, episodes, podcast_id)
        logger.info(
            "Podcast load complete title=%s id=%s uploaded=%d",
            podcast_title,
            podcast_id,
            len(episodes),
        )
        return len(episodes), 0
    except Exception:
        logger.exception(
            "Failed to load podcast episodes. title=%s id=%s",
            podcast_title,
            podcast_id,
        )
        return 0, len(episodes)


def load_all_episodes(bucket: str, entries: list[dict]) -> None:
    """Load all new episodes to S3 as JSON files."""

    logger.info("Starting episode load for %d podcasts", len(entries))
    s3_client = get_s3_client()
    total_uploaded = 0
    total_failed = 0

    for podcast_episode_data in entries:
        uploaded_count, failed_count = load_podcast_episodes(
            s3_client,
            bucket,
            podcast_episode_data,
        )
        total_uploaded += uploaded_count
        total_failed += failed_count

    logger.info(
        "Episode load complete. total_uploaded=%d total_failed=%d",
        total_uploaded,
        total_failed,
    )
