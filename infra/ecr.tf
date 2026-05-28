locals {
  ecr_keys = ["extract"]
}

resource "aws_ecr_repository" "repositories" {
  for_each             = toset(local.ecr_keys)
  name                 = "${var.project_name}-${each.key}"
  image_tag_mutability = var.ecr_image_tag_mutability

  image_scanning_configuration {
    scan_on_push = var.ecr_scan_on_push
  }

  encryption_configuration {
    encryption_type = "AES256"
  }

  tags = merge(
    {
      for key, value in var.common_tags : key => value
      if key != "Project"
    },
    {
      Service = "podcast-analysis"
    }
  )
}

resource "aws_ecr_lifecycle_policy" "repositories" {
  for_each       = aws_ecr_repository.repositories
  repository     = each.value.name
  policy         = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Expire untagged images after ${var.ecr_image_retention_days} days"
        selection = {
          tagStatus       = "untagged"
          countType       = "sinceImagePushed"
          countUnit       = "days"
          countNumber     = var.ecr_image_retention_days
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}
