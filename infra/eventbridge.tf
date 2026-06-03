# ==============================================================================
# EventBridge Scheduler for Step Function Daily Execution
# ==============================================================================

# IAM Role for EventBridge Scheduler
resource "aws_iam_role" "scheduler_role" {
  name = "${var.project_name}-scheduler-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "scheduler.amazonaws.com"
        }
      }
    ]
  })
}

# IAM Policy for EventBridge Scheduler to invoke Step Function
resource "aws_iam_policy" "scheduler_policy" {
  name        = "${var.project_name}-scheduler-policy"
  description = "Policy for EventBridge Scheduler to invoke Step Function"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowStepFunctionExecution"
        Effect = "Allow"
        Action = [
          "states:StartExecution"
        ]
        Resource = "arn:aws:states:${var.aws_region}:*:stateMachine:${var.project_name}-*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "scheduler_attach" {
  role       = aws_iam_role.scheduler_role.name
  policy_arn = aws_iam_policy.scheduler_policy.arn
}

# EventBridge Scheduler Rule - Daily execution at 1am UTC
resource "aws_scheduler_schedule" "daily_pipeline" {
  name                = "${var.project_name}-daily-schedule"
  description         = "Daily trigger for podcast analysis pipeline at 1am UTC"
  schedule_expression = "cron(0 1 * * ? *)"
  state               = "ENABLED"

  flexible_time_window {
    mode = "OFF"
  }

  target {
    arn      = "arn:aws:states:${var.aws_region}:${data.aws_caller_identity.current.account_id}:stateMachine:c23-podex-ai-state-machine"
    role_arn = aws_iam_role.scheduler_role.arn
  }
}

# Data source to get current AWS account ID
data "aws_caller_identity" "current" {}
