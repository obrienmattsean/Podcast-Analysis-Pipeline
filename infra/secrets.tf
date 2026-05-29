# ==============================================================================
# AWS Secrets Manager - Application Secrets
# ==============================================================================
resource "aws_secretsmanager_secret" "app_secrets" {
  name                    = "${var.project_name}-app-secrets"
  description             = "Central encrypted vault for c23-podex-ai database credentials and OpenAI API keys"
  recovery_window_in_days = 0

  tags = merge(
    var.common_tags,
    {
      Component = "secrets-management"
    }
  )
}

resource "aws_secretsmanager_secret_version" "app_secrets_version" {
  secret_id = aws_secretsmanager_secret.app_secrets.id
  secret_string = jsonencode({
    DATABASE_URL    = "postgresql://user:password@hostname:5432/dbname"
    OPENAI_API_KEY  = "sk-placeholder-api-key"
  })
}
