data "aws_vpc" "main" {
  filter {
    name   = "tag:Name"
    values = ["c23-VPC"]
  }
}

data "aws_subnets" "private_subnets" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.main.id]
  }

  filter {
    name   = "tag:Name"
    values = ["*private*"]  # Discovers subnets with "private" in their name
  }
}

data "aws_subnets" "public_subnets" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.main.id]
  }

  filter {
    name   = "tag:Name"
    values = ["*public*"]  # Discovers subnets with "public" in their name
  }
}

# Data source to get current AWS account ID
data "aws_caller_identity" "current" {}