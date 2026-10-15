"""InvenTrack API entry point: health checks, metrics and the inventory routes."""
import logging

from fastapi import Depends, FastAPI, HTTPException
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_session
from app.routes import router
from app.settings import get_settings

settings = get_settings()
logging.basicConfig(level=settings.log_level, format="%(asctime)s %(levelname)-7s %(name)s: %(message)s")
log = logging.getLogger("inventrack")

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Inventory API for InvenTrack. Built by Abhi Gandhi (10397).",
)

# Request counts, latency histograms and in-progress gauges at /metrics
Instrumentator(
    should_group_status_codes=True,
    should_instrument_requests_inprogress=True,
    inprogress_labels=True,
    excluded_handlers=["/metrics"],
).instrument(app).expose(
    app, include_in_schema=False
)


@app.get("/", tags=["meta"])
def index():
    return {"service": settings.app_name, "version": settings.app_version, "docs": "/docs"}


@app.get("/health", tags=["meta"])
def health():
    """Liveness probe. Only says the process is up; never touches the database."""
    return {"status": "ok"}


@app.get("/ready", tags=["meta"])
def ready(session: Session = Depends(get_session)):
    """Readiness probe. Fails with 503 until the database answers."""
    try:
        session.execute(text("SELECT 1"))
    except Exception as exc:  # pragma: no cover - needs a broken database
        log.warning("readiness check failed: %s", exc)
        raise HTTPException(status_code=503, detail="database unavailable") from exc
    return {"status": "ready"}


app.include_router(router)
