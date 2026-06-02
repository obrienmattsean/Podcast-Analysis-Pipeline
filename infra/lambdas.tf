# ==============================================================================
# Transcribe Lambda Function
# ==============================================================================
resource "aws_lambda_function" "transcribe" {
  function_name = "${var.project_name}-transcribe"
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.repositories["transcribe"].repository_url}:latest"
  role          = aws_iam_role.transcribe_role.arn
  timeout       = 900
  memory_size   = 10240

  environment {
    variables = {
      ENVIRONMENT    = var.environment
      S3_BUCKET_NAME = aws_s3_bucket.podcast_bucket.id
      SECRETS_ARN    = aws_secretsmanager_secret.app_secrets.arn
      OPENAI_API_KEY = jsondecode(data.aws_secretsmanager_secret_version.app_secrets.secret_string)["OPENAI_API_KEY"]
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

  environment {
    variables = {
      ENVIRONMENT    = var.environment
      S3_BUCKET_NAME = aws_s3_bucket.podcast_bucket.id
      SECRETS_ARN    = aws_secretsmanager_secret.app_secrets.arn
    }
  }
}



# ==============================================================================
# Vector Lambda Function
# ==============================================================================
resource "aws_lambda_function" "vector" {
  function_name = "${var.project_name}-vector"
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.repositories["vector"].repository_url}:latest"
  role          = aws_iam_role.vector_role.arn
  timeout       = 300
  memory_size   = 1024

  environment {
    variables = {
      ENVIRONMENT    = var.environment
      S3_BUCKET_NAME = aws_s3_bucket.podcast_bucket.id
      SECRETS_ARN    = aws_secretsmanager_secret.app_secrets.arn
      OPENAI_API_KEY = jsondecode(data.aws_secretsmanager_secret_version.app_secrets.secret_string)["OPENAI_API_KEY"]
    }
  }
}
