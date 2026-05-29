import json
import os

from boto3 import client
from dotenv import load_dotenv

load_dotenv()

BUCKET_NAME = os.getenv("S3_BUCKET_NAME")


def get_s3_client() -> client:
  """Return an S3 client using credentials from environment variables."""
  return client(
    "s3",
    region_name=os.getenv("AWS_REGION"),
  )


def get_episode_metadata(episode_key: str, s3_client: client) -> dict:
  """Fetch episode metadata from S3 based on the episode reference."""
  metadata_key = f"{episode_key}/metadata.json"
  try:
    response = s3_client.get_object(Bucket=BUCKET_NAME, Key=metadata_key)
  except s3_client.exceptions.NoSuchKey as err:
    raise ValueError(f"Metadata not found for episode key: {episode_key}") from err

  metadata = response["Body"].read().decode("utf-8")
  return json.loads(metadata)


def get_episode_audio_url(metadata: dict) -> str:
  """Extract the audio file URL from the episode metadata."""
  if "audio_url" not in metadata:
    raise ValueError("Audio URL not found in metadata")
  return metadata.get("audio_url")


# def download_audio(url: str, dest: Path) -> Path:
#   response = requests.get(url)
#   response.raise_for_status()

#   with open(dest, "wb") as f:
#     f.write(response.content)


# def transcribe_audio(file_path: Path) -> str:
#   client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

#   with open(file_path, "rb") as audio_file:
#     response = client.audio.transcriptions.create(
#       file=audio_file,
#       model="whisper-1",
#     )

#   return response


if __name__ == "__main__":
  s3_client = get_s3_client()
  metadata = get_episode_metadata("podcasts/staging/3", s3_client)
  audio_url = get_episode_audio_url(metadata)
  print(f"Audio URL: {audio_url}")

  # print("Downloading audio...")
  # audio_file = download_audio(
  #   "https://content.rss.com/episodes/482/2839578/fluxcapacitor/2026_05_19_13_01_13_46546699-c62e-4301-bcf1-b3ac9fa49c94.mp3",
  #   Path("audio.mp3"),
  # )
  # print("Transcribing audio...")
  # transcription = transcribe_audio(audio_file)
  # print(transcription)
