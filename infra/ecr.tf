locals {
  ecr_keys = ["extract"]
}

resource "aws_ecr_repository" "repositories" {
  for_each             = toset(local.ecr_keys)
  name                 = "${var.project_name}-${each.key}"
  image_tag_mutability = "MUTABLE"

  tags = {
    Environment = var.environment
    Service     = "podcast-analysis"
  }
}
