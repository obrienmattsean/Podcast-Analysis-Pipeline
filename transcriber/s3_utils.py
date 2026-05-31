"""S3 helper utilities for episode metadata and transcript object management."""

import json

import boto3
from pydantic.dataclasses import dataclass


@dataclass
class EpisodeS3:
    bucket: str
    podcast_id: int
    episode_id: int

    @property
    def metadata_key(self) -> str:
        return f"{self.podcast_id}/{self.episode_id}/metadata.json"

    @property
    def transcript_key(self) -> str:
        return f"{self.podcast_id}/{self.episode_id}/transcript.txt"

    def read_metadata(self, s3_client: boto3.S3Client) -> dict:
        response = s3_client.get_object(Bucket=self.bucket, Key=self.metadata_key)
        body_bytes = response["Body"].read()
        return json.loads(body_bytes.decode("utf-8"))

    def get_audio_link(self, s3_client: boto3.S3Client) -> str:
        metadata = self.read_metadata(s3_client)
        audio_link = metadata.get("audio_link")
        if not audio_link or not isinstance(audio_link, str):
            raise ValueError("metadata.json is missing a valid audio_link")
        return audio_link

    def upload_transcript(self, s3_client: boto3.S3Client, transcript: str) -> str:
        s3_client.put_object(
            Bucket=self.bucket,
            Key=self.transcript_key,
            Body=transcript,
            ContentType="text/plain",
        )
        return f"s3://{self.bucket}/{self.transcript_key}"


if __name__ == "__main__":
    s3_client = boto3.client("s3")
    episode = EpisodeS3(bucket="c23-podex-ai-bucket", podcast_id=26, episode_id=199)
    print("Audio link:", episode.get_audio_link(s3_client))
