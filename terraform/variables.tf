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
