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

variable "ecr_image_tag_mutability" {
  description = "Image tag mutability for ECR repositories"
  type        = string
  default     = "MUTABLE"
}

variable "ecr_scan_on_push" {
  description = "Enable image scanning on push"
  type        = bool
  default     = true
}

variable "ecr_image_retention_days" {
  description = "Days to retain untagged images before expiration"
  type        = number
  default     = 5
}

variable "ecr_keep_last_images" {
  description = "Number of tagged images to retain"
  type        = number
  default     = 10
}

variable "lambda_timeout" {
  description = "Lambda function timeout in seconds"
  type        = number
  default     = 60
}

variable "lambda_memory_size" {
  description = "Lambda memory allocation in MB"
  type        = number
  default     = 1024
}

variable "common_tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default = {
    Team = "platform"
  }
}