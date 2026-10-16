# InvenTrack on AWS: a VPC (2 public + 2 private subnets) and an EKS cluster with a managed node group.
data "aws_availability_zones" "available" {
  state = "available"
}

locals {
  name         = "${var.project}-${var.owner}-${var.environment}" # e.g. inventrack-abhi-dev
  cluster_name = "${local.name}-eks"
}

module "network" {
  source = "./modules/network"

  name         = local.name
  cidr         = var.vpc_cidr
  azs          = slice(data.aws_availability_zones.available.names, 0, 2)
  cluster_name = local.cluster_name
}

module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 21.29"

  name               = local.cluster_name
  kubernetes_version = var.kubernetes_version

  vpc_id     = module.network.vpc_id
  subnet_ids = module.network.private_subnet_ids # worker nodes stay off the internet

  endpoint_public_access = true # restrict to your IP for anything beyond a demo

  # Production keeps envelope encryption of Secrets (KMS) and control-plane audit logs.
  # minimal_cost = true drops both for a short demo: no KMS key, no CloudWatch log group.
  encryption_config                        = var.minimal_cost ? null : {}
  create_cloudwatch_log_group              = !var.minimal_cost
  enabled_log_types                        = var.minimal_cost ? [] : ["audit", "api", "authenticator"]
  enable_cluster_creator_admin_permissions = true

  addons = {
    vpc-cni                = { before_compute = true }
    eks-pod-identity-agent = { before_compute = true }
    coredns                = {}
    kube-proxy             = {}
    metrics-server         = {} # needed by the InvenTrack HPA
  }

  eks_managed_node_groups = {
    general = {
      instance_types = var.node_instance_types
      capacity_type  = "ON_DEMAND"
      # Use the default AMI release for kubernetes_version instead of a live SSM lookup,
      # so plans are reproducible; bump kubernetes_version to upgrade nodes.
      use_latest_ami_release_version = false
      min_size                       = var.node_count.min
      desired_size                   = var.node_count.desired
      max_size                       = var.node_count.max
      labels                         = { workload = "inventrack" }
    }
  }
}
