# ==============================================================================
# ECS Task Definition for Streamlit Dashboard
# ==============================================================================
resource "aws_ecs_task_definition" "streamlit" {
  family                   = "c23-ecs-cluster-dashboard"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = aws_iam_role.ecs_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([
    {
      name      = "streamlit-ui"
      image     = "${aws_ecr_repository.repositories["streamlit-ui"].repository_url}:latest"
      essential = true

      portMappings = [
        {
          containerPort = 8501
          hostPort      = 8501
          protocol      = "tcp"
        }
      ]

      environment = [
        {
          name  = "ENVIRONMENT"
          value = var.environment
        },
        {
          name  = "S3_BUCKET_NAME"
          value = aws_s3_bucket.podcast_bucket.id
        },
        {
          name  = "SECRETS_ARN"
          value = aws_secretsmanager_secret.app_secrets.arn
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = "/ecs/c23-ecs-cluster-dashboard"
          "awslogs-region"        = "eu-west-2"
          "awslogs-stream-prefix" = "ecs"
        }
      }
    }
  ])

  tags = merge(
    var.common_tags,
    {
      Name        = "c23-ecs-cluster-dashboard"
      Environment = var.environment
    }
  )
}
