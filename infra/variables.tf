variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "eu-west-2"
}

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "c23-podex-ai"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "s3_bucket_name" {
  description = "Name of the S3 bucket for podcast data (must be globally unique)"
  type        = string
  default     =  "c23-podex-ai-bucket"
}

variable "vpc_id" {
  description = "VPC ID where RDS will be deployed"
  type        = string
  default     = "vpc-08c6b21a04bd32897"
}

variable "db_subnet_ids" {
  description = "List of subnet IDs for DB subnet group (minimum 2 in different AZs)"
  type        = list(string)
  default     = ["subnet-0678fc725e502c0db", "subnet-05c765bee37fe057c","subnet-01629af9db8837650"] # Replace with private subnet IDs in final product
}

variable "db_master_username" {
  description = "Master username for RDS"
  type        = string
  sensitive   = true
}

variable "db_master_password" {
  description = "Master password for RDS"
  type        = string
  sensitive   = true
}

variable "rds_ingress_cidr_blocks" {
  description = "CIDR blocks allowed to access RDS"
  type        = list(string)
  default     = ["0.0.0.0/0"] # Replace with specific CIDR blocks for better security when deploying.
}

variable "rds_database_name" {
  description = "Name of the initial database to create in RDS"
  type        = string
  default     = "c23_podcast_analysis_db" # Replace with your desired database name
}