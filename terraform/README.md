# Terraform

```
terraform/
├── modules/network/      # shared: VPC, 2 public + 2 private subnets, IGW, 1 NAT gateway, EKS subnet tags
├── main.tf …             # AWS root: network module + EKS cluster + managed node group (ap-south-1)
├── localstack_override.tf.example   # copy to *_override.tf to plan the AWS root against LocalStack
└── local/                # no-cloud root: same network module on LocalStack + a kind cluster in place of EKS
```

## AWS (`terraform/`)

- **VPC** `10.40.0.0/16` across 2 AZs. Public subnets `10.40.101.0/24` and `10.40.102.0/24`, private subnets `10.40.1.0/24` and `10.40.2.0/24`. One NAT gateway (cheaper; production would use one per AZ).
- **EKS** `inventrack-dev-eks` (Kubernetes 1.34) with the control plane log group, KMS secrets encryption and add-ons (`vpc-cni`, `coredns`, `kube-proxy`, `eks-pod-identity-agent`, `metrics-server`).
- **Managed node group** `general`: `t3.medium`, min 2 / desired 2 / max 4, in the **private** subnets.
- Credentials come only from `aws configure` or the environment. `terraform.tfvars` is gitignored, and only `terraform.tfvars.example` is committed.

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
terraform init && terraform plan && terraform apply
aws eks update-kubeconfig --region ap-south-1 --name inventrack-dev-eks
terraform destroy      # EKS and the NAT gateway bill by the hour
```

## Running it without an AWS account

I didn't apply this to a real AWS account. EKS and NAT gateways cost money every hour, and the project doesn't need a paid account. Instead:

1. **Static checks, no credentials:** `terraform fmt -check`, `init` and `validate` pass for both roots. CI runs them on every push.
2. **Plan the real AWS config offline:** [LocalStack](https://localstack.cloud) 4.14 (community) emulates the AWS APIs in Docker. With `localstack_override.tf` in place, `terraform plan` of the **unchanged** VPC + EKS root resolves every data source and plans **57 resources**, including the EKS cluster, node group, IAM roles, KMS key and security groups.
3. **Real apply/destroy cycle (`terraform/local/`):** the **same `modules/network`** is applied to LocalStack's EC2 API: VPC, 4 subnets, IGW, NAT, EIP and route tables. A `kind_cluster` with 1 control plane + 2 workers stands in for EKS, because EKS isn't in the free LocalStack edition. `terraform apply` creates 20 resources. The VPC and subnets can then be queried with `aws ec2 describe-*` against LocalStack, and `kubectl get nodes` shows the 3 nodes Ready. `terraform destroy` removes everything.

```bash
docker run -d --name localstack -p 4566:4566 localstack/localstack:4.14
cd terraform/local && terraform init && terraform plan -out=tfplan && terraform apply tfplan
export KUBECONFIG=$PWD/inventrack-local-k8s.kubeconfig && kubectl get nodes
terraform destroy
```

Being honest about the limits: LocalStack emulates the API calls, so the IDs are real LocalStack IDs, but no AWS hardware or network exists. The EKS cluster was planned, not created. The kind cluster is a real Kubernetes cluster, and it's the same kind of target the app was deployed to everywhere else in this project.

## Evidence

`fmt`, `validate` (both roots):

![terraform validate](../screenshots/terraform-validate.png)

`terraform plan` of the **AWS VPC + EKS** root against LocalStack, 57 to add:

![terraform plan aws eks](../screenshots/terraform-plan-aws-eks.png)

`terraform plan` of the local root, 20 to add:

![terraform plan local](../screenshots/terraform-plan-local.png)

`terraform apply`, 20 added, with the cluster outputs:

![terraform apply](../screenshots/terraform-apply.png)

VPC, 2 public + 2 private subnets and the NAT gateway as the AWS CLI sees them, and the 3 kind nodes Ready:

![vpc subnets nodes](../screenshots/terraform-vpc-cluster.png)

`terraform destroy`, 20 destroyed, no VPC left:

![terraform destroy](../screenshots/terraform-destroy.png)
