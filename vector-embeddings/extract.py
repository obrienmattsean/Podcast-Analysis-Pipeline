import logging
import os
from pathlib import PurePosixPath

import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()

S3_BUCKET = os.getenv("S3_BUCKET_NAME")
AWS_REGION = os.getenv("AWS_REGION", "eu-west-2")

if not S3_BUCKET:
    raise RuntimeError("S3_BUCKET_NAME is not set")


def get_s3_client():
    return boto3.client("s3", region_name=AWS_REGION)


def fetch_transcript_from_s3(transcript_key: str, local_path: str = "./tmp/transcript.txt") -> None:
    """Download transcript.txt from S3 to a local file."""

    s3_client = get_s3_client()

    # Normalize key safely (removes leading slash issues and joins path correctly)
    clean_key = transcript_key.lstrip("/")
    key = str(PurePosixPath(clean_key) / "transcript.txt")
    os.makedirs("./tmp", exist_ok=True)
    try:
        print(local_path)
        s3_client.download_file(S3_BUCKET, key, local_path)
        print(f"Downloaded s3://{S3_BUCKET}/{key} → {local_path}")
        logger.info("Downloaded s3://%s/%s → %s", S3_BUCKET, key, local_path)
    except ClientError as e:
        logger.error("Failed to download s3://%s/%s: %s", S3_BUCKET, key, e)
        raise


if __name__ == "__main__":
    episode_key = "26/199/"  # or "26/199" or "/26/199/" — all now safe
    fetch_transcript_from_s3(episode_key)
