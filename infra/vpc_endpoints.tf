# Data source to get private route tables
data "aws_route_tables" "private" {
  vpc_id = data.aws_vpc.main.id

  filter {
    name   = "tag:Name"
    values = ["*private*"]
  }
}

# ==============================================================================
# VPC Endpoints for ECS/ECR in Private Subnets
# ==============================================================================

# Security group for VPC endpoints
resource "aws_security_group" "vpc_endpoints" {
  name        = "${var.project_name}-vpc-endpoints-sg"
  description = "Security group for VPC endpoints"
  vpc_id      = data.aws_vpc.main.id

  ingress {
    from_port       = 443
    to_port         = 443
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_tasks.id]
    description     = "Allow HTTPS from ECS tasks"
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
      Name        = "${var.project_name}-vpc-endpoints-sg"
      Environment = var.environment
    }
  )
}

# S3 VPC Endpoint (for pulling image layers)
resource "aws_vpc_endpoint" "s3" {
  vpc_id            = data.aws_vpc.main.id
  service_name      = "com.amazonaws.${var.aws_region}.s3"
  vpc_endpoint_type = "Gateway"

  route_table_ids = data.aws_route_tables.private.ids

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = "*"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::*",
          "arn:aws:s3:::*/*"
        ]
      }
    ]
  })

  tags = merge(
    var.common_tags,
    {
      Name        = "${var.project_name}-s3-endpoint"
      Environment = var.environment
    }
  )
}

# CloudWatch Logs VPC Endpoint (for task logs)
resource "aws_vpc_endpoint" "logs" {
  vpc_id            = data.aws_vpc.main.id
  service_name      = "com.amazonaws.${var.aws_region}.logs"
  vpc_endpoint_type = "Interface"

  subnet_ids         = data.aws_subnets.private_subnets.ids
  security_group_ids = [aws_security_group.vpc_endpoints.id]

  tags = merge(
    var.common_tags,
    {
      Name        = "${var.project_name}-logs-endpoint"
      Environment = var.environment
    }
  )
}

# Secrets Manager VPC Endpoint (for accessing secrets)
resource "aws_vpc_endpoint" "secrets_manager" {
  vpc_id            = data.aws_vpc.main.id
  service_name      = "com.amazonaws.${var.aws_region}.secretsmanager"
  vpc_endpoint_type = "Interface"

  subnet_ids         = data.aws_subnets.private_subnets.ids
  security_group_ids = [aws_security_group.vpc_endpoints.id]

  tags = merge(
    var.common_tags,
    {
      Name        = "${var.project_name}-secrets-manager-endpoint"
      Environment = var.environment
    }
  )
}
