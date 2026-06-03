# ==============================================================================
# EventBridge Scheduler for Step Function Daily Execution
# ==============================================================================

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
