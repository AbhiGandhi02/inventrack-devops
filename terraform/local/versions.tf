terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.69"
    }
    kind = {
      source  = "tehcyx/kind"
      version = "~> 0.11"
    }
  }
}

# The AWS provider talks to LocalStack (an AWS API emulator in Docker) instead of real AWS.
# No account, no credentials, no cost. The dummy keys below are what LocalStack expects.
provider "aws" {
  region                      = var.region
  access_key                  = "test"
  secret_key                  = "test"
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true
  s3_use_path_style           = true

  endpoints {
    ec2 = var.localstack_endpoint
    iam = var.localstack_endpoint
    sts = var.localstack_endpoint
  }

  default_tags {
    tags = {
      Project     = var.project
      Environment = var.environment
      Owner       = "abhi-gandhi-10397"
      ManagedBy   = "terraform"
    }
  }
}

provider "kind" {}
