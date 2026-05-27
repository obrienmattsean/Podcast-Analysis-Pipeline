# This backend stores Terraform state in S3 for team collaboration and safety.
terraform {
  backend "s3" {
    bucket = "c23-podex-ai-terraform-state"
    key    = "podcast-analysis/terraform.tfstate"
    region = "eu-west-2"
    encrypt = true
  }
}