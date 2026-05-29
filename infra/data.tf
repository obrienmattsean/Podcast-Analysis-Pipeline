data "aws_vpc" "main" {
  filter {
    name   = "tag:Name"
    values = ["c23*"]  # Discovers VPC with name like "podcast-vpc"
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

data "aws_vpc" "existing" {
  filter {
    name   = "tag:Name"
    values = ["c23-vpc"]
  }
}