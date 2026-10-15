# Kubernetes and Helm

Everything here ran on a local **kind** cluster: 1 control plane and 2 workers (`kubernetes/kind/cluster.yaml`). The same chart deploys to EKS (`terraform/`) by changing the values file.

## Cluster setup

```bash
kind create cluster --config kubernetes/kind/cluster.yaml        # host :8080 -> ingress
helm upgrade --install ingress-nginx ingress-nginx/ingress-nginx -n ingress-nginx --create-namespace \
  --set controller.hostPort.enabled=true --set controller.service.type=NodePort \
  --set-string controller.nodeSelector.ingress-ready=true \
  --set 'controller.tolerations[0].key=node-role.kubernetes.io/control-plane' \
  --set 'controller.tolerations[0].operator=Exists' --set 'controller.tolerations[0].effect=NoSchedule'
helm upgrade --install metrics-server metrics-server/metrics-server -n kube-system \
  --set 'args={--kubelet-insecure-tls}'                          # needed by the HPA

docker compose build && kind load docker-image inventrack-backend:local inventrack-frontend:local --name inventrack
kubectl apply -f k8s/namespace.yaml
helm upgrade --install inventrack helm/inventrack -n inventrack -f helm/inventrack/values-local.yaml --wait
```

Open http://inventrack.local:8080. Add `127.0.0.1 inventrack.local` to `/etc/hosts`, or use `curl -H 'Host: inventrack.local' localhost:8080`.

## What the chart (`helm/inventrack`) creates

| Object | Notes |
|---|---|
| `Deployment/inventrack-api` | 2–5 replicas (HPA), rolling update `maxUnavailable: 0`, startup / liveness (`/health`) / readiness (`/ready`, checks the DB) probes, read-only root FS, non-root, all capabilities dropped, seccomp `RuntimeDefault` |
| `Deployment/inventrack-web` | 2 replicas, `/healthz` probes |
| `StatefulSet/inventrack-db` | PostgreSQL 16 with a 1 Gi PVC, `pg_isready` probes |
| `Service` × 3 | All `ClusterIP` |
| `Ingress` | host `inventrack.local`: `/api` → API, `/` → web |
| `HorizontalPodAutoscaler` | CPU target 60%, min 2, max 5 |
| `PodDisruptionBudget` | At least 1 API pod survives voluntary disruptions |
| `ConfigMap`, `Secret` | Log level. DB password is random on first install, reused on upgrades, `resource-policy: keep` |
| `Job/…-migrate` | `alembic upgrade head` as a `post-install,post-upgrade` hook (Argo CD runs it as PostSync), so migrations run once, not in every pod |
| `ServiceMonitor` | Optional: Prometheus scrapes `/metrics` on every API pod |

The `inventrack` namespace enforces the **restricted** Pod Security Standard, so a pod that runs as root or keeps capabilities is rejected.

| Values file | Use |
|---|---|
| `values.yaml` | Defaults. Images from GHCR, tag set by CI |
| `values-local.yaml` | kind / minikube with locally built `:local` images, `pullPolicy: Never` |
| `values-gitops.yaml` | Argo CD. CI writes the commit SHA here. Uses the pre-created `inventrack-db` Secret |

`helm lint` passes for both value sets (it's also a CI job).

## Evidence

After the GitOps hand-over (Argo CD manages the release, so it no longer appears in `helm list`), during a load test:

![nodes, pods, services, ingress, HPA, PVC, helm list](../screenshots/k8s-resources.png)

![App through the Ingress](../screenshots/k8s-app-ingress.png)

Under `scripts/load-test.sh` (24 workers for 6 minutes through the Ingress), the HPA scaled the API from 2 to 5 pods, then back down once the load stopped:

![HPA scaled to 5](../screenshots/hpa-scaling.png)
