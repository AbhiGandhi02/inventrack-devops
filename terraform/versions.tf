terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.69"
    }
  }
}

provider "aws" {
  region = var.region
  # Credentials come from `aws configure` / the environment - never from this repository

  default_tags {
    tags = {
      Project     = var.project
      Environment = var.environment
      Owner       = var.owner_full_name
      ManagedBy   = "terraform"
    }
  }
}
