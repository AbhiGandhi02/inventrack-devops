#!/usr/bin/env bash
# Generates steady API traffic so Grafana, the alerts and the HPA have data to show.
#   ./scripts/load-test.sh [base-url] [seconds] [parallel]
#   HOST_HEADER=inventrack.local ./scripts/load-test.sh http://localhost:8080 180 20
BASE="${1:-http://localhost:8000}"
DURATION="${2:-60}"
PARALLEL="${3:-8}"
HEADERS=()
[[ -n "${HOST_HEADER:-}" ]] && HEADERS=(-H "Host: $HOST_HEADER")

worker() {
  local stop=$((SECONDS + DURATION))
  while (( SECONDS < stop )); do
    curl -s -o /dev/null "${HEADERS[@]}" "$BASE/api/items"
    curl -s -o /dev/null "${HEADERS[@]}" "$BASE/api/summary"
    curl -s -o /dev/null "${HEADERS[@]}" "$BASE/api/items?search=desk"
    curl -s -o /dev/null "${HEADERS[@]}" "$BASE/api/items?reorder_only=true"
    curl -s -o /dev/null "${HEADERS[@]}" "$BASE/api/items/999999"   # deliberate 404
  done
}

echo "Load: $PARALLEL workers against $BASE for ${DURATION}s"
for _ in $(seq "$PARALLEL"); do worker & done
wait
echo "Finished."
