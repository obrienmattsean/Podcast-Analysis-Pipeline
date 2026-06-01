"""Extract transcript and episode metadata from S3 storage.

This module handles S3 operations for retrieving podcast transcripts
and extracting episode identifiers from S3 paths.
"""

import logging
import os
from urllib.parse import urlparse

import boto3
from botocore.client import BaseClient
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

S3_BUCKET = os.getenv("S3_BUCKET_NAME", "c23-podex-ai-bucket")
AWS_REGION = os.getenv("AWS_REGION", "eu-west-2")


def get_s3_client() -> BaseClient:
    """Get an S3 client instance for AWS interactions.

    Returns:
        An S3 client configured for the specified AWS region.
    """
    return boto3.client("s3", region_name=AWS_REGION)


def parse_s3_path(s3_path: str) -> str:
    """Parse S3 path into object key.

    Args:
        s3_path: S3 URI in format s3://bucket/path.

    Returns:
        The object key (path without leading slash).

    Raises:
        ValueError: If the S3 path has invalid format or scheme.

    Example:
        >>> parse_s3_path("s3://my-bucket/26/199/")
        '26/199/'
    """
    parsed_url = urlparse(s3_path)
    if parsed_url.scheme != "s3":
        raise ValueError(f"Invalid S3 path: {s3_path}")
    return parsed_url.path.lstrip("/")


def extract_episode_id(s3_path: str) -> int:
    """Extract episode ID from S3 path.

    Assumes S3 path structure: s3://bucket/podcast_id/episode_id/

    Args:
        s3_path: S3 URI containing the episode identifier.

    Returns:
        The integer episode ID extracted from the path.

    Raises:
        ValueError: If path format is invalid or episode ID is not an integer.

    Example:
        >>> extract_episode_id("s3://my-bucket/26/199/")
        199
    """
    key = parse_s3_path(s3_path)
    parts = key.split("/")
    if len(parts) < 3:
        raise ValueError(f"Invalid S3 path for episode ID extraction: {s3_path}")
    try:
        episode_id = int(parts[-2])
        return episode_id
    except ValueError as e:
        raise ValueError(f"Episode ID is not an integer in S3 path: {s3_path}") from e


def fetch_transcript_from_s3(s3_client: BaseClient, s3_path: str) -> str:
    """Fetch transcript content from S3 storage.

    Args:
        s3_client: Initialized S3 client from boto3.
        s3_path: S3 URI where transcript.txt is located.

    Returns:
        The transcript text content as a string.

    Raises:
        ClientError: If S3 operation fails (file not found, permission denied, etc.).

    Example:
        >>> transcript = fetch_transcript_from_s3(s3_client, "s3://bucket/26/199/")
        >>> len(transcript) > 0
        True
    """
    try:
        key = parse_s3_path(s3_path)
        transcript = s3_client.get_object(Bucket=S3_BUCKET, Key=key + "transcript.txt")

        logger.info("Fetched s3://%s/%s", S3_BUCKET, key + "transcript.txt")
        return transcript.get("Body").read().decode("utf-8")
    except ClientError as e:
        logger.error("Failed to fetch s3://%s/%s: %s", S3_BUCKET, key + "transcript.txt", e)
        raise
