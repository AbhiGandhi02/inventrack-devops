output "vpc_id" {
  description = "VPC ID"
  value       = module.network.vpc_id
}

output "public_subnet_ids" {
  description = "The two public subnets"
  value       = module.network.public_subnet_ids
}

output "private_subnet_ids" {
  description = "The two private subnets (EKS nodes)"
  value       = module.network.private_subnet_ids
}

output "cluster_name" {
  description = "EKS cluster name"
  value       = module.eks.cluster_name
}

output "cluster_endpoint" {
  description = "EKS API endpoint"
  value       = module.eks.cluster_endpoint
}

output "kubeconfig_command" {
  description = "Run this to point kubectl at the cluster"
  value       = "aws eks update-kubeconfig --region ${var.region} --name ${module.eks.cluster_name}"
}
