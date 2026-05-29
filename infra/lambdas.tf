# ==============================================================================
# Transcribe Lambda Function
# ==============================================================================
resource "aws_lambda_function" "transcribe" {
  function_name = "${var.project_name}-transform"
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.repositories["transcribe"].repository_url}:latest"
  role          = aws_iam_role.transform_role.arn
  timeout       = 900
  memory_size   = 2048

  environment {
    variables = {
      ENVIRONMENT    = var.environment
      S3_BUCKET_NAME = aws_s3_bucket.podcast_bucket.id
      SECRETS_ARN    = aws_secretsmanager_secret.app_secrets.arn
    }
  }
}
