# Docker

`docker/docker-compose.yml` runs the full stack. The root `docker-compose.yml` includes it, so `docker compose up --build` works from the repository root.

| Service | Image | Port | Runs as | Health check |
|---|---|---|---|---|
| `db` | `postgres:16-alpine` | internal 5432 | postgres | `pg_isready` |
| `backend` | built from `application/backend` | `8000` | `inventrack` (uid 10001) | `GET /health` |
| `frontend` | built from `application/frontend` | `3000` → 8080 (`FRONTEND_PORT` to change) | `nginx` (uid 101) | `GET /healthz` |

Start-up order comes from `depends_on: condition: service_healthy`: the database becomes healthy, then the backend runs `alembic upgrade head` and becomes healthy, then the frontend starts.

```bash
docker compose up --build -d
./scripts/seed.sh http://localhost:8000      # sample inventory
open http://localhost:3000
docker compose ps
docker compose down          # keep data
docker compose down -v       # also delete the database volume
```

## Images

**Backend** (`python:3.12-slim`): dependencies are installed in their own layer before the code is copied, so code changes don't reinstall packages. It creates a fixed non-root user (10001:10001) so Kubernetes can verify `runAsNonRoot`, and it has a `HEALTHCHECK`.

**Frontend** (multi-stage):
1. `node:22-alpine` runs `npm ci && npm run build`.
2. `nginxinc/nginx-unprivileged:1.29-alpine` serves `dist/` on port 8080 as uid 101. `apk upgrade` pulls in Alpine security fixes (this cleared 43 HIGH CVEs, see `security/README.md`). nginx proxies `/api/` to `${BACKEND_URL}`, which is filled in at container start, and adds basic security headers.

Neither image runs as root:

![compose ps and id](../screenshots/docker-compose-up.png)
