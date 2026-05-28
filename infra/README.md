# Podcast Analysis Infrastructure

Terraform configuration for the podcast analysis pipeline.

## Resources

- **`c23-podex-ai-bucket`** — S3 bucket for podcast transcripts (versioned, encrypted, private)

## First-Time Setup

The S3 backend (`backend.tf`) stores Terraform state in `c23-podex-ai-terraform-state`. This bucket must be created manually before running Terraform for the first time.

### 1. Create the state bucket manually

```bash
aws s3api create-bucket \
  --bucket c23-podex-ai-terraform-state \
  --region eu-west-2 \
  --create-bucket-configuration LocationConstraint=eu-west-2

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket c23-podex-ai-terraform-state \
  --versioning-configuration Status=Enabled

# Block public access
aws s3api put-public-access-block \
  --bucket c23-podex-ai-terraform-state \
  --public-access-block-configuration "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
```

### 2. Create a terraform.tfvars file

Create a file that will hold all your secrets by following the terraform.tfvars.example file template.

### 3. Deploy the infrastructure

```bash
terraform init
terraform apply

