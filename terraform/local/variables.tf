variable "localstack_endpoint" {
  description = "LocalStack edge URL"
  type        = string
  default     = "http://localhost:4566"
}

variable "region" {
  description = "Region the emulated AWS APIs use"
  type        = string
  default     = "ap-south-1"
}

variable "project" {
  type    = string
  default = "inventrack"
}

variable "environment" {
  type    = string
  default = "local"
}

variable "vpc_cidr" {
  type    = string
  default = "10.40.0.0/16"
}

variable "kubernetes_node_image" {
  description = "kind node image (Kubernetes version) for the stand-in cluster"
  type        = string
  default     = "kindest/node:v1.34.0"
}

variable "worker_count" {
  description = "Worker nodes, mirroring the EKS node group's desired size"
  type        = number
  default     = 2
}
