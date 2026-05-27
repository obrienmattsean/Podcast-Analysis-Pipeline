# S3 Bucket for podcast transcripts
resource "aws_s3_bucket" "podcast_bucket" {
  bucket = var.s3_bucket_name
}

resource "aws_s3_bucket_public_access_block" "podcast_bucket" {
  bucket = aws_s3_bucket.podcast_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
