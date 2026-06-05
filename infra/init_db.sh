#!/usr/bin/env bash
# reset.sh — Drops and recreates all database tables, then empties the S3 bucket.
# Reads credentials from .env in the same directory as this script.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/.env"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Error: .env file not found at $ENV_FILE" >&2
  exit 1
fi

# shellcheck disable=SC1090
set -o allexport
source "$ENV_FILE"
set +o allexport

: "${RDS_HOST:?RDS_HOST is not set}"
: "${RDS_DBNAME:?RDS_DBNAME is not set}"
: "${RDS_USER:?RDS_USER is not set}"
: "${RDS_PASSWORD:?RDS_PASSWORD is not set}"
: "${S3_BUCKET_NAME:?S3_BUCKET_NAME is not set}"
: "${AWS_REGION:=eu-west-2}"

echo "WARNING: This will permanently delete all data in:"
echo "  RDS database : $RDS_DBNAME on $RDS_HOST"
echo "  S3 bucket    : s3://$S3_BUCKET_NAME"
read -r -p "Type 'yes' to confirm: " CONFIRM
if [[ "$CONFIRM" != "yes" ]]; then
  echo "Aborted."
  exit 0
fi

# ── Database reset ──────────────────────────────────────────────────────────
echo ""
echo "Resetting database..."
PGPASSWORD="$RDS_PASSWORD" psql \
  --host="$RDS_HOST" \
  --username="$RDS_USER" \
  --dbname="$RDS_DBNAME" \
  --port=5432 \
  --file="$SCRIPT_DIR/schema.sql"
echo "Database reset complete."

# ── S3 bucket empty ─────────────────────────────────────────────────────────
echo ""
echo "Emptying S3 bucket s3://$S3_BUCKET_NAME ..."
aws s3 rm "s3://$S3_BUCKET_NAME" \
  --recursive \
  --region "$AWS_REGION"
echo "S3 bucket empty."

echo ""
echo "Reset complete."
