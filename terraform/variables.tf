variable "region" {
  description = "AWS region"
  type        = string
  default     = "ap-south-1"
}

variable "project" {
  description = "Project name, used as a prefix"
  type        = string
  default     = "inventrack"
}

variable "owner" {
  description = "Short owner name, included in every resource name"
  type        = string
  default     = "abhi"
}

variable "owner_full_name" {
  description = "Owner tag value"
  type        = string
  default     = "Abhi Gandhi - 10397"

  validation {
    # IAM tag values only allow letters, numbers, spaces and _ . : / = + - @
    condition     = can(regex("^[\\p{L}\\p{Z}\\p{N}_.:/=+\\-@]*$", var.owner_full_name))
    error_message = "owner_full_name may only contain letters, numbers, spaces and _ . : / = + - @ (no parentheses)."
  }
}

variable "minimal_cost" {
  description = "Skip billable extras (KMS key for secrets encryption, control-plane log group) for short-lived demo clusters"
  type        = bool
  default     = false
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.40.0.0/16"
}

variable "kubernetes_version" {
  description = "EKS control plane version"
  type        = string
  default     = "1.34"
}

variable "node_instance_types" {
  description = "EC2 instance types for the managed node group"
  type        = list(string)
  default     = ["t3.medium"]
}

variable "node_count" {
  description = "Node group size"
  type = object({
    min     = number
    desired = number
    max     = number
  })
  default = { min = 2, desired = 2, max = 4 }

  validation {
    condition     = var.node_count.min <= var.node_count.desired && var.node_count.desired <= var.node_count.max
    error_message = "node_count must satisfy min <= desired <= max."
  }
}
