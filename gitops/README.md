# GitOps with Argo CD

Git is the source of truth for what runs in the cluster. Nothing is applied by hand: CI writes a new image tag into Git, and Argo CD makes the cluster match.

```
push to main ─► CI: test, scan, build, push ghcr.io/…:<sha> ─► gitops-bump job commits <sha> to
helm/inventrack/values-gitops.yaml ─► Argo CD sees the commit ─► helm render ─► rolling update
```

## Setup (once)

```bash
helm repo add argo https://argoproj.github.io/argo-helm
helm upgrade --install argocd argo/argo-cd -n argocd --create-namespace \
  --set configs.params."server\.insecure"=true --set dex.enabled=false

kubectl apply -f k8s/namespace.yaml
# Argo CD renders Helm without cluster access, so the chart can't generate and remember a DB password.
# Create the Secret once (or keep the one a previous `helm install` left behind - it has resource-policy: keep):
kubectl create secret generic inventrack-db -n inventrack --from-literal=password="$(openssl rand -hex 16)"

kubectl apply -f gitops/argocd-application.yaml
kubectl port-forward -n argocd svc/argocd-server 8090:80
kubectl get secret -n argocd argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d
```

The GHCR packages inherit the repository's **public** visibility, so the cluster pulls them without an image pull secret.

## Application settings (`argocd-application.yaml`)

- **source:** this repo, `main`, `helm/inventrack` with `values.yaml` + `values-gitops.yaml`
- **automated sync** with `prune: true` (objects deleted from Git are deleted from the cluster) and `selfHeal: true` (manual edits are reverted)
- **retry** with backoff, so a sync that starts while PostgreSQL is still booting tries again
- the chart's migration Job is a Helm hook, and Argo CD runs it as a **PostSync** hook

**Rollback** is a `git revert` of the bump commit. Argo CD then deploys the previous SHA.

## Live run (v1.1)

I pushed commit `57fb395` ("Release v1.1"). CI built and pushed new images, and the `gitops-bump` job committed the new SHA. Argo CD synced it and rolled the pods without any manual step:

![Argo CD application synced and healthy](../screenshots/argocd-app.png)

![v1.1 live](../screenshots/gitops-v1.1-live.png)
