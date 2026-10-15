# DevSecOps

Every push runs these checks. The **security gate** job needs all of them to pass, and only after the gate are images pushed to GHCR.

| Check | Tool | Fails the build when |
|---|---|---|
| SAST (Python) | Bandit `-ll` | Any medium or high finding in `application/backend/app` |
| SAST (Python + JS) | GitHub CodeQL | Results are uploaded to the Security tab |
| SCA (Python) | pip-audit | A dependency in `requirements.txt` has a known vulnerability |
| SCA (Node) | `npm audit --audit-level=high` | A high or critical advisory |
| Secrets | Gitleaks v8.30.1 | A credential pattern anywhere in the tree |
| Container images | Trivy, `severity: HIGH,CRITICAL`, `ignore-unfixed: true`, `exit-code: 1` | A **fixable** HIGH/CRITICAL CVE in either image |

Images are built once, saved as a tarball and passed between jobs as an artifact. The scanned bytes are exactly the bytes that get pushed and deployed. Nothing is rebuilt after the scan.

## What Trivy found, and the fix

Trivy checks OS packages (Alpine `apk`, Debian `dpkg`) and language packages (Python wheels, npm) inside the image.

**Before:** I built the frontend on `nginxinc/nginx-unprivileged:1.29-alpine` *without* `apk upgrade`. Trivy reported **43 HIGH** vulnerabilities, all in Alpine 3.23.4 packages that already had fixed versions. Examples:

| Package | CVE | Installed → fixed | Issue |
|---|---|---|---|
| c-ares | CVE-2026-33630 | 1.34.6-r0 → 1.34.8-r0 | Use-after-free / double-free in query completion |
| curl | CVE-2026-11352 | 8.17.0-r1 → 8.22.0-r0 | Remote DoS via the QUIC receive path |
| curl | CVE-2026-12064 | 8.17.0-r1 → 8.22.0-r0 | SSH host verification bypass with schemeless SFTP/SCP URLs |

None of these came from my code. They came from the base image, which lagged behind Alpine's security repository. The gate exited with code 1.

![Trivy before: 43 HIGH](../screenshots/trivy-frontend-before-fix.png)

**Fix:** in the runtime stage, switch to root just long enough to run `apk upgrade --no-cache`, then go back to uid 101. The rebuilt image has **0** fixable HIGH/CRITICAL issues:

![Trivy after: 0](../screenshots/trivy-frontend-after-fix.png)

The backend (`python:3.12-slim`, Debian 13) was clean from the start, both OS packages and every Python package:

![Trivy backend: 0](../screenshots/trivy-backend-clean.png)

Locally, `./security/scan-images.sh` runs the same gate on both images.

## Other hardening

- Non-root images (10001 / 101), and the namespace enforces Pod Security `restricted`
- Read-only root filesystem for the API, `allowPrivilegeEscalation: false`, `drop: [ALL]`, seccomp `RuntimeDefault`
- No secrets in Git. The DB password is generated in-cluster, `.env` and `terraform.tfvars` are gitignored, and Terraform reads cloud credentials from the environment
- The GitHub token gets least privilege per job (`contents: read` by default, `packages: write` only for the push job, `contents: write` only for the GitOps commit)
