output "podcast_bucket_name" {
  description = "Name of the S3 bucket for podcast transcripts"
  value       = aws_s3_bucket.podcast_bucket.bucket
}

output "podcast_bucket_arn" {
  description = "ARN of the S3 bucket for podcast transcripts"
  value       = aws_s3_bucket.podcast_bucket.arn
}

output "extract_lambda_arn" {
  description = "ARN of the extraction Lambda function"
  value       = aws_lambda_function.extract.arn
}

output "extract_lambda_function_name" {
  description = "Name of the extraction Lambda function"
  value       = aws_lambda_function.extract.function_name
}

output "lambda_execution_role_arn" {
  description = "ARN of the Lambda execution IAM role"
  value       = aws_iam_role.lambda_execution_role.arn
}
