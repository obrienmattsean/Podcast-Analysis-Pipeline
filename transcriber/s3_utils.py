"""S3 helper utilities for episode metadata and transcript object management."""

import json

import boto3
from pydantic import Field
from pydantic.dataclasses import dataclass


@dataclass
class EpisodeS3:
    """
    Data class representing an episode's S3 location and related operations."""

    uri: str = Field(
        ..., description="S3 URI for the episode, e.g. s3://bucket/podcast_id/episode_id/"
    )

    @property
    def bucket(self) -> str:
        """Extract the S3 bucket name from the episode URI."""
        return self.uri.split("/")[2]

    @property
    def podcast_id(self) -> str:
        """Extract the podcast ID from the episode URI."""
        return self.uri.split("/")[3]

    @property
    def episode_id(self) -> str:
        """Extract the episode ID from the episode URI."""
        return self.uri.split("/")[4]

    @property
    def metadata_key(self) -> str:
        """Construct the S3 key for the episode's metadata.json file."""
        return f"{self.podcast_id}/{self.episode_id}/metadata.json"

    @property
    def transcript_key(self) -> str:
        """Construct the S3 key for the episode's transcript.txt file."""
        return f"{self.podcast_id}/{self.episode_id}/transcript.txt"

    def read_metadata(self, s3_client: boto3.client) -> dict:
        """Read and parse the episode's metadata.json from S3."""
        response = s3_client.get_object(Bucket=self.bucket, Key=self.metadata_key)
        body_bytes = response["Body"].read()
        return json.loads(body_bytes.decode("utf-8"))

    def get_audio_link(self, s3_client: boto3.client) -> str:
        """Extract the audio link from the episode's metadata."""
        metadata = self.read_metadata(s3_client)
        audio_link = metadata.get("audio_link")
        if not audio_link or not isinstance(audio_link, str):
            raise ValueError("metadata.json is missing a valid audio_link")
        return audio_link

    def upload_transcript(self, s3_client: boto3.client, transcript: str) -> str:
        """Upload the transcript text to S3 and return the S3 URI of the uploaded transcript."""
        s3_client.put_object(
            Bucket=self.bucket,
            Key=self.transcript_key,
            Body=transcript,
            ContentType="text/plain",
        )
        return f"s3://{self.bucket}/{self.transcript_key}"


if __name__ == "__main__":
    s3_client = boto3.client("s3")
    episode = EpisodeS3(uri="s3://c23-podex-ai-bucket/26/199/")
    print("Audio link:", episode.get_audio_link(s3_client))
