FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /srv

# Dependencies first so this layer stays cached while the code changes
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY alembic.ini ./
COPY alembic ./alembic
COPY app ./app

# Fixed numeric non-root user, so Kubernetes runAsNonRoot can verify it
RUN groupadd --gid 10001 inventrack \
 && useradd --uid 10001 --gid 10001 --no-create-home --shell /usr/sbin/nologin inventrack
USER 10001:10001

EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=3s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(urllib.request.urlopen('http://127.0.0.1:8000/health').status != 200)"

# Docker Compose: migrate, then serve. Kubernetes overrides this and migrates in a Helm hook Job.
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port 8000"]
