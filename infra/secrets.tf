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

# NOTE: Do not manage secret values in Terraform state or commit them to VCS.
# Populate the secret value out-of-band (e.g., via CI or:
#   aws secretsmanager put-secret-value --secret-id ${var.project_name}-app-secrets --secret-string '{"DATABASE_URL":"...","OPENAI_API_KEY":"..."}'
# ).
