# Podex AI Daily Pipeline Lambda

Scheduled Lambda that discovers and ingests new podcast episodes daily.

## Purpose

Orchestrates the complete ETL pipeline to find new episodes from RSS feeds for all tracked podcasts and add them to the database. Runs daily (typically 0 AM UTC via EventBridge). Can also be invoked through a POST request when an user wants to add a new RSS feed to be tracked

Enables the transcription, summarization, and embedding pipelines by ensuring most up-to-date episode data.

## How It Works

1. **Extract**:
   - Queries database for all monitored podcasts
   - Fetches RSS feed for each podcast
   - Parses episode entries

2. **Model**:
    - Defines a pydantic model called ValidatedEpisode that requires correct types
    - Checks that published date is not in the future
    - Checks that audio url is valid

2. **Transform**:
   - Locates audio urls
   - Validates episode data (titles, URLs, publish dates) using ValidatedEpisode

3. **Load**:
   - Inserts new episodes into RDS database
   - Inserts new episodes metadata into a S3 bucket to be processed later for transcription
   - Returns a list of uploaded S3 paths



## Setup

### Prerequisites

- RDS PostgreSQL with schema deployed
- Network access from Lambda to RDS
- Tracked podcasts already in database

### Environment Variables

```
RDS_HOST               # Database host (required)
RDS_DBNAME             # Database name (required)
RDS_USERNAME           # Database username (required)
RDS_PASSWORD           # Database password (required)
RDS_PORT               # Database port (default: 5432)
S3_BUCKET_NAME         # S3 Bucket name (required)
AWS_REGION             # AWS region (default: eu-west-2)
```

### Installation

```bash
pip install -r requirements.txt
```

### Local Testing

```bash
# Create .env file with database credentials
export RDS_HOST=localhost
export RDS_DBNAME=podexai
export RDS_USERNAME=postgres
export RDS_PASSWORD=password
export S3_BUCKET_NAME=podexai

python handler.py
```

## Dependencies

- psycopg2-binary - PostgreSQL adapter
- feedparser - RSS feed parsing
- pydantic - Data validation
- python-dotenv - Environment variables

## Key Functions

- `extract_new_episodes()`: Fetches and parses RSS feeds
- `transform_all_podcast_episodes()`: Validates and formats episode data
- `load_all_episodes()`: Inserts episodes with upload paths to S3
- `lambda_handler(event, context)`: Main entry point

## Lambda Response

```json
{
  "statusCode": 200,
  "message": "success",
  "uploaded_paths": ["s3://bucket/1/1/", "s3://bucket/1/2/"]
}
```


## Pushing to ECR with Docker

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) installed and running
- A `.env` file in the root directory

### Steps

1. Navigate to the `extractor` directory:

   ```bash
   cd extractor
   ```

2. Make the script executable (first time only):

   ```bash
   chmod +x push.sh
   ```

3. Run the script:

   ```bash
   ./push.sh
   ```