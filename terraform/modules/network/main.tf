# Shared network layout, used by both the AWS root (../../) and the LocalStack root (../../local):
# one VPC, 2 public + 2 private subnets across 2 AZs, internet gateway, one NAT gateway.
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 6.7"

  name = "${var.name}-vpc"
  cidr = var.cidr
  azs  = var.azs

  public_subnets  = [for i, _ in var.azs : cidrsubnet(var.cidr, 8, i + 101)] # 10.40.101.0/24, 10.40.102.0/24
  private_subnets = [for i, _ in var.azs : cidrsubnet(var.cidr, 8, i + 1)]   # 10.40.1.0/24,   10.40.2.0/24

  enable_nat_gateway   = true
  single_nat_gateway   = true # one NAT keeps the bill small; production would use one per AZ
  enable_dns_hostnames = true
  enable_dns_support   = true

  # Lets the AWS load balancer controller find the right subnets for Services/Ingresses
  public_subnet_tags = {
    "kubernetes.io/role/elb"                    = 1
    "kubernetes.io/cluster/${var.cluster_name}" = "shared"
  }
  private_subnet_tags = {
    "kubernetes.io/role/internal-elb"           = 1
    "kubernetes.io/cluster/${var.cluster_name}" = "shared"
  }
}
