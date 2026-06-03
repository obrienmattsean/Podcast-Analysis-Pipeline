# ==============================================================================
# ECS Task Definition for Streamlit Dashboard
# ==============================================================================
resource "aws_security_group" "ecs_tasks" {
  name        = "${var.project_name}-ecs-tasks-sg"
  description = "Security group for ECS tasks"
  vpc_id      = data.aws_vpc.main.id

  ingress {
    from_port   = 8501
    to_port     = 8501
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow Streamlit dashboard access"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound traffic"
  }

  tags = merge(
    var.common_tags,
    {
      Name        = "${var.project_name}-ecs-tasks-sg"
      Environment = var.environment
    }
  )
}

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

# ==============================================================================
# ECS Service for Dashboard
# ==============================================================================
resource "aws_ecs_service" "dashboard" {
  name            = "c23-dashboard-service"
  cluster         = "c23-ecs-cluster"
  task_definition = aws_ecs_task_definition.streamlit.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = data.aws_subnets.private_subnets.ids
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = false
  }

  tags = merge(
    var.common_tags,
    {
      Name        = "c23-dashboard-service"
      Environment = var.environment
    }
  )

  depends_on = [aws_ecs_task_definition.streamlit]
}
