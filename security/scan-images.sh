#!/usr/bin/env bash
# Local copy of the CI image gate: build both images and fail on fixable HIGH/CRITICAL CVEs.
# Usage (from the repository root): ./security/scan-images.sh
# Needs Docker and either the trivy CLI or the aquasec/trivy image.
set -uo pipefail
trivy_scan() {
  if command -v trivy >/dev/null; then
    trivy image --severity HIGH,CRITICAL --ignore-unfixed --exit-code 1 "$1"
  else
    docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy:0.75.0 \
      image --severity HIGH,CRITICAL --ignore-unfixed --exit-code 1 "$1"
  fi
}

failed=()
for component in backend frontend; do
  image="inventrack-$component:scan"
  echo "==> building $image"
  docker build -q -t "$image" "application/$component" >/dev/null || { failed+=("$component (build)"); continue; }
  echo "==> scanning $image"
  trivy_scan "$image" || failed+=("$component")
done

if ((${#failed[@]})); then
  echo "GATE FAILED: ${failed[*]}"
  exit 1
fi
echo "Both images passed the HIGH/CRITICAL gate."
