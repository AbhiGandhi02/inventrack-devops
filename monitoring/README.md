# Monitoring

## Metrics from the app

`prometheus-fastapi-instrumentator` exposes these at `GET /metrics`:

- `http_requests_total{handler, method, status}`, with status grouped as `2xx/4xx/5xx`
- `http_request_duration_seconds_bucket{handler, method, le}`, a latency histogram
- `http_requests_inprogress{handler, method}`, in-flight requests

`tests/test_health.py::test_metrics_are_in_prometheus_format` checks the endpoint in CI.

![curl /metrics](../screenshots/metrics-endpoint.png)

## Stack

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm upgrade --install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
  -n monitoring --create-namespace -f monitoring/prometheus-values.yaml -f monitoring/grafana-values.yaml
kubectl apply -f monitoring/alert-rules.yaml -f monitoring/grafana-dashboard.yaml
# make the app scrapeable (values-gitops.yaml already enables this)
helm upgrade inventrack helm/inventrack -n inventrack --reuse-values --set metrics.serviceMonitor.enabled=true

kubectl port-forward -n monitoring svc/kube-prometheus-stack-prometheus 9090:9090
kubectl port-forward -n monitoring svc/kube-prometheus-stack-grafana 3300:80
kubectl get secret -n monitoring kube-prometheus-stack-grafana -o jsonpath='{.data.admin-password}' | base64 -d
```

The chart's **ServiceMonitor** selects the API Service, so Prometheus scrapes every API pod, including pods the HPA adds:

![Prometheus targets](../screenshots/prometheus-targets.png)

## Dashboard: "InvenTrack - Application Overview"

`grafana-dashboard.yaml` is a ConfigMap labelled `grafana_dashboard: "1"`. Grafana's sidecar imports it automatically. It has 15 panels in 3 rows:

- **Golden signals:** API pods scraped, requests/s, 4xx share, 5xx share, p95 latency, API replicas
- **Traffic:** requests/s by endpoint, responses by status class (stacked), p50/p95/p99 latency, in-flight requests
- **Saturation:** CPU by pod, memory by pod, HPA current/desired/max replicas

![Grafana dashboard](../screenshots/grafana-dashboard.png)

## Alerts (`alert-rules.yaml`)

| Alert | Fires when | Severity |
|---|---|---|
| `InventrackApiDown` | No API target is up for 1 m | critical |
| `InventrackApiReplicasDegraded` | Fewer than 2 API replicas available for 3 m | warning |
| `InventrackPodCrashLooping` | A pod restarts more than twice in 10 m | warning |
| `InventrackHigh5xxRate` | More than 5% of responses are 5xx for 2 m | warning |
| `InventrackSlowResponses` | API p95 above 750 ms for 5 m | warning |
| `InventrackApiAtMaxReplicas` | HPA pinned at max for 10 m | info |

![Alert rules loaded](../screenshots/prometheus-alert-rules.png)
