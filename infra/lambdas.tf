# ==============================================================================
# Extract Lambda Function
# ==============================================================================
resource "aws_lambda_function" "extract" {
  function_name = "${var.project_name}-extract"
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.repositories["extract"].repository_url}:latest"
  role          = aws_iam_role.extract_role.arn
  timeout       = 300
  memory_size   = 512

  vpc_config {
    subnet_ids         = data.aws_subnets.private_subnets.ids
    security_group_ids = [aws_security_group.app_sg.id]
  }

  environment {
    variables = {
      ENVIRONMENT     = var.environment
      S3_BUCKET_NAME  = aws_s3_bucket.podcast_bucket.id
      SECRETS_ARN     = aws_secretsmanager_secret.app_secrets.arn
    }
  }
}
