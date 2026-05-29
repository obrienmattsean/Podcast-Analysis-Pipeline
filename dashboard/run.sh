#!/usr/bin/env bash
set -euo pipefail

echo "Building Docker image for Streamlit dashboard..."
docker buildx build --platform linux/amd64 --provenance=false --load -t podcast-dashboard:latest .

echo "Running Streamlit dashboard container..."
docker rm -f podcast-dashboard || true

ENV_FILE_FLAG=""
if [ -f .env ]; then
  ENV_FILE_FLAG="--env-file .env"
fi

docker run -d --name podcast-dashboard -p 8501:8501 --restart unless-stopped $ENV_FILE_FLAG podcast-dashboard:latest
echo "Streamlit dashboard is running at http://localhost:8501"