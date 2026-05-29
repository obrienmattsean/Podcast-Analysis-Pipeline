"""Lambda entrypoint for S3-driven podcast transcription orchestration."""

import logging
import os
import tempfile
from pathlib import Path
from typing import Any

from audio_utils import download_audio_file
from s3_utils import (
    extract_audio_link,
    get_s3_client,
    parse_episode_s3_uri,
    read_episode_metadata,
    upload_transcript_text,
)
from transcribe import transcribe_audio_to_text

logger = logging.getLogger(__name__)


def handler(event: str | dict[str, Any] | None = None, context: Any = None) -> dict[str, Any]:
    """Process an episode S3 URI and upload transcript text to the same prefix.

    Args:
        event: Episode S3 URI as a string. Dict input with episode_s3_uri is
            also supported for backward compatibility.
        context: Lambda runtime context (unused in local execution).

    Returns:
        dict[str, Any]: Response payload with statusCode, message, and episode_uri.

    Example:
        >>> handler("s3://c23-podex-ai-bucket/21/93/", None)
        {'statusCode': 200, 'message': 'Transcription successful.', 'episode_uri': 's3://c23-podex-ai-bucket/21/93/'}
    """

    episode_s3_uri: str | None = None
    if isinstance(event, str):
        episode_s3_uri = event
    elif isinstance(event, dict):
        value = event.get("episode_s3_uri")
        if isinstance(value, str):
            episode_s3_uri = value

    if not episode_s3_uri:
        return {
            "statusCode": 400,
            "message": "Event must be a non-empty episode S3 URI string",
        }

    location = parse_episode_s3_uri(episode_s3_uri)
    s3_client = get_s3_client()

    metadata = read_episode_metadata(s3_client, location)
    audio_url = extract_audio_link(metadata)

    transcribe_model = os.getenv("TRANSCRIBE_MODEL", "whisper-1")
    chunk_length_minutes = int(os.getenv("CHUNK_LENGTH_MINUTES", "10"))

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        source_audio_path = download_audio_file(audio_url, temp_path / "audio.mp3")
        transcript = transcribe_audio_to_text(
            source_audio_path=source_audio_path,
            chunks_output_dir=temp_path / "chunks",
            transcribe_model=transcribe_model,
            chunk_length_minutes=chunk_length_minutes,
        )

    upload_transcript_text(s3_client, location, transcript)
    s3_client.close()

    return {
        "statusCode": 200,
        "message": "Transcription successful.",
        "episode_uri": episode_s3_uri,
    }
