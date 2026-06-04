#!/usr/bin/env bash
set -euo pipefail

REGION="eu-west-2"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REPO_NAME="c23-podex-ai-streamlit-ui"

echo "Logging in to ECR..."
aws ecr get-login-password --region "$REGION" | \
  docker login --username AWS --password-stdin "${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com"

echo "Building $REPO_NAME Docker image..."
docker buildx build --platform linux/amd64 --provenance=false -t "${REPO_NAME}:latest" .

echo "Tagging ${REPO_NAME} image for ECR..."
docker tag "${REPO_NAME}:latest" "${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${REPO_NAME}:latest"

echo "Pushing ${REPO_NAME} image to ECR..."
docker push "${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${REPO_NAME}:latest"

echo "Docker image for ${REPO_NAME} has been pushed to ECR successfully."
