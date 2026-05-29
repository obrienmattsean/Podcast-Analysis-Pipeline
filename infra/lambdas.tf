# ==============================================================================
# Lambda Function - Extract
# ==============================================================================
resource "aws_lambda_function" "extract" {
  function_name = "${var.project_name}-extract"
  package_type  = "Image"
  role          = aws_iam_role.extract_role.arn
  image_uri     = "${aws_ecr_repository.repositories["extract"].repository_url}:latest"

  timeout     = 300
  memory_size = var.lambda_memory_size

  vpc_config {
    subnet_ids         = data.aws_subnets.private_subnets.ids
    security_group_ids = [aws_security_group.rds.id]
  }

  environment {
    variables = {
      S3_BUCKET_NAME = aws_s3_bucket.podcast_bucket.id
    }
  }

  tags = merge(
    var.common_tags,
    {
      Component = "pipeline-extraction"
    }
  )

  depends_on = [
    aws_iam_role_policy_attachment.extract_policy_attachment
  ]
}
