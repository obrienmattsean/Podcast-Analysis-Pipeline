"""Lambda entrypoint for S3-driven podcast transcription orchestration."""

import logging
import tempfile
from pathlib import Path
from typing import Any

import boto3
from audio_utils import download_audio_file
from s3_utils import EpisodeS3
from transcribe import transcribe


def handler(event: dict, context: Any) -> dict[str, Any]:
    """Process an episode S3 URI and upload transcript text to the same prefix.

    Args:
        event: Dictionary containing the S3 URL of the episode.

        context: Lambda runtime context (unused in local execution).

    Returns:
        dict[str, Any]: Response payload with statusCode, message, and episode_uri.
    """

    with tempfile.TemporaryDirectory() as temp_dir:
        s3_client = boto3.client("s3")

        episode_s3_uri = event["episode_s3_url"]
        episode_s3 = EpisodeS3(episode_s3_uri)

        logging.info("Starting transcription for episode: %s", episode_s3_uri)

        audio_url = episode_s3.get_audio_link(s3_client)
        logging.info("Resolved audio URL: %s", audio_url)

        audio_path = download_audio_file(audio_url, Path(temp_dir) / "audio.mp3")
        logging.info("Audio downloaded to: %s", audio_path)

        transcript = transcribe(audio_path)
        logging.info("Transcription complete (%d characters)", len(transcript))

        episode_s3.upload_transcript(s3_client, transcript)
        logging.info("Transcript uploaded to S3: %s", episode_s3_uri)

        s3_client.close()

        return {
            "statusCode": 200,
            "message": "Transcription successful.",
            "episode_uri": episode_s3_uri,
        }


if __name__ == "__main__":
    # Example local execution with a test S3 URI
    test_event = {"episode_s3_url": "s3://c23-podex-ai-bucket/17/246/"}
    response = handler(test_event, None)
    print(response)
