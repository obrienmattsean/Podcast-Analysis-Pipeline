output "podcast_bucket_name" {
  description = "Name of the S3 bucket for podcast transcripts"
  value       = aws_s3_bucket.podcast_bucket.bucket
}

output "podcast_bucket_arn" {
  description = "ARN of the S3 bucket for podcast transcripts"
  value       = aws_s3_bucket.podcast_bucket.arn
}
