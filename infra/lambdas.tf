# ==============================================================================
# Transcribe Lambda Function
# ==============================================================================
resource "aws_lambda_function" "transcribe" {
  function_name = "${var.project_name}-transcribe"
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.repositories["transcribe"].repository_url}:latest"
  role          = aws_iam_role.transcribe_role.arn
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

# ==============================================================================
# Enrich Lambda Function
# ==============================================================================
resource "aws_lambda_function" "enrich" {
  function_name = "${var.project_name}-enrich"
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.repositories["enrich"].repository_url}:latest"
  role          = aws_iam_role.enrich_role.arn
  timeout       = 180
  memory_size   = 512

  vpc_config {
    subnet_ids         = data.aws_subnets.private_subnets.ids
    security_group_ids = [aws_security_group.app_sg.id]
  }

  environment {
    variables = {
      ENVIRONMENT    = var.environment
      S3_BUCKET_NAME = aws_s3_bucket.podcast_bucket.id
      SECRETS_ARN    = aws_secretsmanager_secret.app_secrets.arn
    }
  }
}
