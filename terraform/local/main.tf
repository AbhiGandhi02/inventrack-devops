# No-cloud twin of ../main.tf
#   network: the SAME ../modules/network module, applied to LocalStack's emulated EC2 API
#   cluster: a kind cluster with 1 control plane + N workers stands in for EKS
#            (EKS is not part of LocalStack's free community edition)
locals {
  name         = "${var.project}-${var.environment}"
  cluster_name = "${local.name}-k8s"
}

data "aws_availability_zones" "available" {
  state = "available"
}

module "network" {
  source = "../modules/network"

  name         = local.name
  cidr         = var.vpc_cidr
  azs          = slice(data.aws_availability_zones.available.names, 0, 2)
  cluster_name = local.cluster_name
}

resource "kind_cluster" "this" {
  name            = local.cluster_name
  node_image      = var.kubernetes_node_image
  wait_for_ready  = true
  kubeconfig_path = abspath("${path.module}/${local.cluster_name}.kubeconfig")

  kind_config {
    kind        = "Cluster"
    api_version = "kind.x-k8s.io/v1alpha4"

    node {
      role = "control-plane"
    }

    dynamic "node" {
      for_each = range(var.worker_count)
      content {
        role   = "worker"
        labels = { workload = "inventrack" }
      }
    }
  }
}
