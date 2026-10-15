variable "name" {
  description = "Prefix for resource names"
  type        = string
}

variable "cidr" {
  description = "VPC CIDR block"
  type        = string
}

variable "azs" {
  description = "Exactly two availability zones"
  type        = list(string)

  validation {
    condition     = length(var.azs) == 2
    error_message = "The network module expects exactly two availability zones."
  }
}

variable "cluster_name" {
  description = "Kubernetes cluster name, used in subnet discovery tags"
  type        = string
}
