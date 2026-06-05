# ==============================================================================
# ECS Task Definition for Streamlit Dashboard
# ==============================================================================
resource "aws_security_group" "ecs_tasks" {
  name        = "${var.project_name}-ecs-tasks-sg"
  description = "Security group for ECS tasks"
  vpc_id      = data.aws_vpc.main.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow HTTP from load balancer"
  }

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
  family                   = "c23-podex-ai-dashboard-ecs"
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
          "awslogs-create-group"  = "true"
          "awslogs-region"        = var.aws_region
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

data "aws_ecs_cluster" "podex_host_cluster" {
  cluster_name = var.cluster_name
}

resource "aws_ecs_service" "dashboard" {
  name            = "c23-dashboard-service"
  cluster         = var.cluster_name
  task_definition = aws_ecs_task_definition.streamlit.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = data.aws_subnets.public_subnets.ids
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.streamlit.arn
    container_name   = "streamlit-ui"
    container_port   = 8501
  }

  tags = merge(
    var.common_tags,
    {
      Name        = "c23-dashboard-service"
      Environment = var.environment
    }
  )

  depends_on = [aws_ecs_task_definition.streamlit, aws_lb_listener.streamlit]
}

# ==============================================================================
# Network Load Balancer for Dashboard
# ==============================================================================
resource "aws_lb" "streamlit" {
  name               = "${var.project_name}-dashboard-nlb"
  internal           = false
  load_balancer_type = "network"
  subnets            = data.aws_subnets.public_subnets.ids

  enable_deletion_protection = false

  tags = merge(
    var.common_tags,
    {
      Name        = "${var.project_name}-dashboard-nlb"
      Environment = var.environment
    }
  )
}

resource "aws_lb_target_group" "streamlit" {
  name        = "${var.project_name}-streamlit-tg"
  port        = 8501
  protocol    = "TCP"
  vpc_id      = data.aws_vpc.main.id
  target_type = "ip"

  health_check {
    protocol            = "TCP"
    port                = "8501"
    healthy_threshold   = 2
    unhealthy_threshold = 2
    interval            = 10
    timeout             = 5
  }

  deregistration_delay = 30

  tags = merge(
    var.common_tags,
    {
      Name        = "${var.project_name}-streamlit-tg"
      Environment = var.environment
    }
  )
}

resource "aws_lb_listener" "streamlit" {
  load_balancer_arn = aws_lb.streamlit.arn
  port              = "80"
  protocol          = "TCP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.streamlit.arn
  }
}
