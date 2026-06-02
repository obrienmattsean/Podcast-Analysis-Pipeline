
# ==============================================================================
# Security Group for Application (Lambda)
# ==============================================================================
resource "aws_security_group" "app_sg" {
  name        = "${var.project_name}-app-sg"
  description = "Security group for application (Lambda) instances"
  vpc_id      = data.aws_vpc.main.id

  # Allow all outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound traffic"
  }

  tags = {
    Name        = "${var.project_name}-app-sg"
    Environment = var.environment
  }
}

# ==============================================================================
# Security Group for RDS
# ==============================================================================
resource "aws_security_group" "rds" {
  name        = "${var.project_name}-podcast-analysis-rds-sg"
  description = "Security group for Podcast Analysis RDS instance"
  vpc_id      = data.aws_vpc.main.id  # Auto-discovered VPC



  # Allow inbound from application security group
  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.app_sg.id]
    description     = "PostgreSQL from application security group"
  }

  # Allow inbound from specific CIDR blocks
  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = var.rds_ingress_cidr_blocks # Replace the variable with specific CIDR blocks for better security when deploying defaults to all.
    description = "PostgreSQL from allowed CIDR blocks"
  }

  # Allow all outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound traffic"
  }

  tags = {
    Name        = "${var.project_name}-podcast-analysis-rds-sg"
    Environment = var.environment
  }
}

# ==============================================================================
# DB Subnet Group
# ==============================================================================
# This groups the subnets where RDS is allowed to be deployed
resource "aws_db_subnet_group" "podcast_analysis" {
  name       = "${var.project_name}-podcast-analysis-db-subnet-group"
  subnet_ids = data.aws_subnets.public_subnets.ids  # Auto-discovered public subnets (MVP - restrict in production)

  tags = {
    Name        = "${var.project_name}-podcast-analysis-db-subnet-group"
    Environment = var.environment
  }
}

# ==============================================================================
# RDS PostgreSQL Instance
# ==============================================================================
resource "aws_db_instance" "podcast_analysis" {
  identifier            = "${var.project_name}-podcast-analysis-db"
  engine                = "postgres"
  instance_class        = "db.t3.micro"  
  allocated_storage     = 20  
  max_allocated_storage = 100  

  # Database and authentication
  db_name  = var.rds_database_name 
  username = var.db_master_username
  password = var.db_master_password

  # Network configuration
  db_subnet_group_name   = aws_db_subnet_group.podcast_analysis.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  publicly_accessible    = true  # CHANGE THIS - JUST FOR INITIAL DEPLOYMENT

  # Storage and performance
  storage_type          = "gp3"  # General purpose (good for MVP)
  storage_encrypted     = true  # Encrypt data at rest
  # For MVP with small storage, using gp3 defaults is fine

  # Backup and maintenance
  backup_retention_period = 7  # Keep 7 days of backups (reasonable for MVP)
  backup_window           = "03:00-04:00"  # UTC time
  maintenance_window      = "mon:04:00-mon:05:00"  # UTC time
  skip_final_snapshot     = false  # Create final snapshot on deletion
  final_snapshot_identifier = "c23-podcast-analysis-db-final-snapshot"

  # Performance insights and monitoring (lite tier is free)
  performance_insights_enabled = true
  monitoring_interval          = 60
  monitoring_role_arn          = aws_iam_role.rds_monitoring.arn

  # Minor version upgrades
  auto_minor_version_upgrade = false  # Manual control over upgrades

  tags = {
    Name        = "${var.project_name}-rds"
    Environment = var.environment
    Purpose     = "Podcast Analysis Pipeline"
  }

  depends_on = [aws_db_subnet_group.podcast_analysis]
}

## PostgreSQL pgvector extension setup
# For MVP, create the extension manually after RDS is ready:
# psql -h <endpoint> -U postgres -d c23_podcast_analysis_db --set=sslmode=require
# Then run: CREATE EXTENSION IF NOT EXISTS vector;

