"""S3 helper utilities for episode metadata and transcript object management."""

import json
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

import boto3

EXPECTED_BUCKET = "c23-podex-ai-bucket"


@dataclass(frozen=True)
class EpisodeS3Location:
    """Container for a normalized episode S3 location.

    Attributes:
        bucket: S3 bucket name.
        prefix: Episode prefix in form "podcast_id/episode_id".
    """

    bucket: str
    prefix: str

    @property
    def metadata_key(self) -> str:
        """Return the metadata object key for this episode prefix."""
        return f"{self.prefix}/metadata.json"

    @property
    def transcript_key(self) -> str:
        """Return the transcript object key for this episode prefix."""
        return f"{self.prefix}/transcript.txt"


def get_s3_client() -> Any:
    """Create an S3 client using environment-based AWS configuration.

    Returns:
        Any: A boto3 S3 client instance.
    """

    return boto3.client("s3")


def parse_episode_s3_uri(
    episode_s3_uri: str, expected_bucket: str = EXPECTED_BUCKET
) -> EpisodeS3Location:
    """Parse and validate an episode S3 URI into a normalized location.

    Args:
        episode_s3_uri: Input URI, for example s3://c23-podex-ai-bucket/21/93/.
        expected_bucket: Required bucket name for validation.

    Returns:
        EpisodeS3Location: Parsed bucket and normalized episode prefix.

    Raises:
        ValueError: If the URI is invalid, bucket mismatches, or path format is unsupported.

    Example:
        >>> parse_episode_s3_uri("s3://c23-podex-ai-bucket/21/93/")
        EpisodeS3Location(bucket='c23-podex-ai-bucket', prefix='21/93')
    """

    parsed = urlparse(episode_s3_uri)
    if parsed.scheme != "s3" or not parsed.netloc:
        raise ValueError("episode_s3_uri must be a valid S3 URI")

    bucket = parsed.netloc
    if bucket != expected_bucket:
        raise ValueError(f"episode_s3_uri bucket must be {expected_bucket}")

    path_parts = [part for part in parsed.path.strip("/").split("/") if part]
    if len(path_parts) != 2:
        raise ValueError("episode_s3_uri path must be in format /podcast_id/episode_id/")

    prefix = f"{path_parts[0]}/{path_parts[1]}"
    return EpisodeS3Location(bucket=bucket, prefix=prefix)


def read_episode_metadata(s3_client: Any, location: EpisodeS3Location) -> dict:
    """Read and decode metadata.json for an episode location.

    Args:
        s3_client: boto3-compatible S3 client.
        location: Parsed episode S3 location.

    Returns:
        dict: Decoded metadata payload from metadata.json.
    """

    response = s3_client.get_object(Bucket=location.bucket, Key=location.metadata_key)
    body_bytes = response["Body"].read()
    return json.loads(body_bytes.decode("utf-8"))


def extract_audio_link(metadata: dict) -> str:
    """Extract and validate the audio_link field from episode metadata.

    Args:
        metadata: Metadata dictionary loaded from S3.

    Returns:
        str: HTTP(S) URL to the episode audio file.

    Raises:
        ValueError: If audio_link is missing or not a string.
    """

    audio_link = metadata.get("audio_link")
    if not audio_link or not isinstance(audio_link, str):
        raise ValueError("metadata.json is missing a valid audio_link")
    return audio_link


def upload_transcript_text(s3_client: Any, location: EpisodeS3Location, transcript: str) -> str:
    """Upload transcript text next to metadata.json for an episode.

    Args:
        s3_client: boto3-compatible S3 client.
        location: Parsed episode S3 location.
        transcript: Plain-text transcript content.

    Returns:
        str: S3 URI where transcript.txt was written.
    """

    s3_client.put_object(
        Bucket=location.bucket,
        Key=location.transcript_key,
        Body=transcript,
        ContentType="text/plain",
    )
    return f"s3://{location.bucket}/{location.transcript_key}"
