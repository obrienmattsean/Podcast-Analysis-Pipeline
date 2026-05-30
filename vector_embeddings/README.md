# Vector Embeddings

AWS Lambda function that processes podcast transcripts into vector embeddings for semantic search (RAG pipeline).

## Overview

Implements an ETL pipeline triggered by an S3 upload event:

1. **Extract** — Fetches the transcript from S3
2. **Transform** — Chunks the transcript and generates embeddings via OpenAI
3. **Load** — Inserts the embedded chunks into PostgreSQL (RDS)

## Modules

| File | Responsibility |
|------|----------------|
| `handler.py` | Lambda entry point; orchestrates the ETL pipeline |
| `extract.py` | Fetches transcript text and episode ID from S3 |
| `transform.py` | Chunks transcript and generates embeddings via OpenAI API |
| `load.py` | Inserts embedded chunks into the RDS `episode_chunks` table |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | OpenAI API key for embedding generation |
| `S3_BUCKET_NAME` | S3 bucket containing podcast transcripts |
| `AWS_REGION` | AWS region (default: `eu-west-2`) |
| `RDS_HOST` | PostgreSQL host |
| `RDS_DBNAME` | PostgreSQL database name |
| `RDS_USER` | PostgreSQL username |
| `RDS_PASSWORD` | PostgreSQL password |
| `RDS_PORT` | PostgreSQL port (default: `5432`) |

## S3 Path Convention

Transcripts must follow the path structure:

```
s3://<S3_BUCKET_NAME>/<series_id>/<episode_id>/transcript.txt
```

The episode ID is extracted from the second-to-last path segment.

## Lambda Event Schema

```json
{
  "upload_path": "s3://c23-podex-ai-bucket/26/199/"
}
```

## Chunking Strategy

Transcripts are split into overlapping token-based chunks using `tiktoken`:

| Parameter | Value |
|-----------|-------|
| Model | `text-embedding-3-small` |
| Chunk size | 800 tokens |
| Overlap | 100 tokens |
| Batch size | 20 chunks per OpenAI API request |

## Local Development

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment

Copy `.env.example` to `.env` and fill in the required values.

### 3. Run locally

```bash
cd vector_embeddings
python handler.py
```

The `__main__` block in `handler.py` contains a sample event for local testing.
