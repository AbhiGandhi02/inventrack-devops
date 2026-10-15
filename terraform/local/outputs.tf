output "vpc_id" {
  value = module.network.vpc_id
}

output "public_subnet_ids" {
  value = module.network.public_subnet_ids
}

output "private_subnet_ids" {
  value = module.network.private_subnet_ids
}

output "cluster_name" {
  value = kind_cluster.this.name
}

output "cluster_endpoint" {
  value = kind_cluster.this.endpoint
}

output "kubeconfig_command" {
  value = "export KUBECONFIG=${kind_cluster.this.kubeconfig_path}"
}
