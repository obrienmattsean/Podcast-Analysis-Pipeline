# Transcriber

AWS Lambda service that transcribes one podcast episode and writes a plain-text transcript back to S3.

## What It Does

1. Accepts an episode S3 URI (for example: `s3://c23-podex-ai-bucket/21/93/`).
2. Reads `metadata.json` from that prefix.
3. Downloads the episode audio from `audio_link` in metadata.
4. Transcribes audio in chunks using OpenAI Whisper.
5. Uploads `transcript.txt` to the same S3 prefix.

## Event Contract

Primary input is a string event:

```json
"s3://c23-podex-ai-bucket/21/93/"
```

Backward-compatible input is also accepted:

```json
{
  "episode_s3_uri": "s3://c23-podex-ai-bucket/21/93/"
}
```

## Lambda Response

Success:

```json
{
  "statusCode": 200,
  "message": "Transcription successful.",
  "episode_uri": "s3://c23-podex-ai-bucket/21/93/"
}
```

Validation error:

```json
{
  "statusCode": 400,
  "message": "..."
}
```

## Required Environment Variables

- `OPENAI_API_KEY`: OpenAI API key.

## Local Run

From this folder:

```bash
python lambda_function.py
```

## Build and Push Image

From this folder:

```bash
./deploy.sh
```

This script builds a linux/amd64 Docker image and pushes it to ECR repository `c23-podex-ai-transcribe` in `eu-west-2`.
