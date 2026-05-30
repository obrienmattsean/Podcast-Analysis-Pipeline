import logging
import os
from urllib.parse import urlparse

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

S3_BUCKET = os.getenv("S3_BUCKET_NAME")
AWS_REGION = os.getenv("AWS_REGION", "eu-west-2")


def get_s3_client() -> boto3.client:
    return boto3.client("s3", region_name=AWS_REGION)


def parse_s3_path(s3_path: str) -> str:
    """Parse S3 path into key."""
    parsed_url = urlparse(s3_path)
    if parsed_url.scheme != "s3":
        raise ValueError(f"Invalid S3 path: {s3_path}")
    key = parsed_url.path.lstrip("/")
    return key


def extract_episode_id(s3_path: str) -> int:
    """Extract episode ID from S3 path."""
    key = parse_s3_path(s3_path)
    parts = key.split("/")
    if len(parts) < 2:
        raise ValueError(f"Invalid S3 path for episode ID extraction: {s3_path}")
    try:
        episode_id = int(parts[-2])
        return episode_id
    except ValueError as e:
        raise ValueError(f"Episode ID is not an integer in S3 path: {s3_path}") from e


def fetch_transcript_from_s3(s3_client, s3_path: str) -> None:
    """Fetch transcript from S3."""
    try:
        key = parse_s3_path(s3_path)
        transcript = s3_client.get_object(Bucket=S3_BUCKET, Key=key + "transcript.txt")

        logger.info("Fetched s3://%s/%s", S3_BUCKET, key + "transcript.txt")
        return transcript.get("Body").read().decode("utf-8")
    except ClientError as e:
        logger.error("Failed to fetch s3://%s/%s: %s", S3_BUCKET, key + "transcript.txt", e)
        raise
