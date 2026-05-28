data "aws_vpc" "main" {
  filter {
    name   = "tag:Name"
    values = ["c23*"]  # Discovers VPC with name like "podcast-vpc"
  }
}

data "aws_subnet_ids" "private_subnets" {
  vpc_id = data.aws_vpc.main.id

  filter {
    name   = "tag:Name"
    values = ["*private*"]  # Discovers subnets with "private" in their name
  }
}

data "aws_subnet_ids" "public_subnets" {
  vpc_id = data.aws_vpc.main.id

  filter {
    name   = "tag:Name"
    values = ["*public*"]  # Discovers subnets with "public" in their name
  }
}