output "podcast_bucket_name" {
  description = "Name of the S3 bucket for podcast transcripts"
  value       = aws_s3_bucket.podcast_bucket.bucket
}

output "podcast_bucket_arn" {
  description = "ARN of the S3 bucket for podcast transcripts"
  value       = aws_s3_bucket.podcast_bucket.arn
}

output "rds_endpoint" {
  description = "RDS instance endpoint"
  value       = aws_db_instance.podcast_analysis.endpoint
}

output "rds_address" {
  description = "RDS instance hostname only"
  value       = aws_db_instance.podcast_analysis.address
}

output "rds_port" {
  description = "RDS instance port"
  value       = aws_db_instance.podcast_analysis.port
}

output "security_group_id" {
  description = "Security group ID for RDS"
  value       = aws_security_group.rds.id
}

output "database_name" {
  description = "RDS database name"
  value       = aws_db_instance.podcast_analysis.db_name
}

output "rds_instance_id" {
  description = "RDS instance identifier"
  value       = aws_db_instance.podcast_analysis.id
}
    