# Enricher and Uploader

AWS Lambda service that enriches data from one podcast episodes transcript and generates keywords, speakers, sentiment score, and a summary which are uploaded to RDS.

## What It Does

1. Accepts an episode S3 URI (for example: `s3://c23-podex-ai-bucket/21/93/`).
2. Reads `metadata.json` and `transcript.txt` from that prefix.
3. Enriches the data from `transcript.txt` using OpenAI gpt-4o-mini.
4. Sorts and organises data ready for upload.
5. Uploads data to `episodes`, `entities` and `episode_entities` tables in RDS.

## Event Contract


```json
{
  "episode_uri": "s3://c23-podex-ai-bucket/21/93/"
}
```

## Lambda Response

Success:

```json
{
  "statusCode": 200,
  "message": "Enrichment upload successful!",
  "episode_id": 93
}
```

Validation error:

```json
{
  "statusCode": 500,
  "message": "Enrichment upload failed..."
}
```

## Required Environment Variables

- `OPENAI_API_KEY`: OpenAI API key.
- `AWS_ACCESS_KEY_ID`: AWS access key.
- `AWS_SECRET_ACCESS_KEY`: AWS secret access key.
- `RDS_HOST`: AWS host.
- `RDS_PORT`: 5432.
- `RDS_DBNAME`: Database name.
- `RDS_USER`: postgres.
- `RDS_PASSWORD`: Database password.
- `REGION_NAME`: AWS region name.

## AWS Permissions

Attach an execution role that allows:

- `s3:GetObject` for episode metadata objects.
- `rds-db:connect`: for uploading and querying the RDS.
Use Lambda execution role credentials (recommended) instead of hardcoded static access keys.

## Local Run

From this folder:

```bash
python enrichment_upload_handler.py
```

## Build and Push Image

From this folder:

```bash
./deploy.sh
```

This script builds a linux/amd64 Docker image and pushes it to ECR repository `c23-podex-ai-enrich` in `eu-west-2`.