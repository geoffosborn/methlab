"""
MethLab API - Continuous Fugitive Methane Monitoring Service
FastAPI Application
Port: 8020
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routes import alerts, auth, dashboard, deks, facilities, reports, sentinel2, storage, tropomi

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("MethLab API starting on port %s...", settings.port)
    yield
    logger.info("MethLab API shutting down...")


app = FastAPI(
    title="MethLab API",
    description="Continuous Fugitive Methane Monitoring Service",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(deks.router)
app.include_router(facilities.router)
app.include_router(tropomi.router)
app.include_router(sentinel2.router)
app.include_router(alerts.router)
app.include_router(reports.router)
app.include_router(storage.router)


@app.get("/health")
async def health_check():
    from methlab_common import health_response

    return health_response("methlab-api")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.port, reload=settings.debug)
