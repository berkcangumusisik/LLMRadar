from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.rest import router as rest_router
from app.api.ws import router as ws_router
from app.core.config import get_settings
from app.ingestion.scheduler import run_initial_fetch, setup_scheduler
from app.realtime.broadcaster import start_broadcaster, stop_broadcaster
from app.realtime.manager import manager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings = get_settings()
    logger.info("Starting %s …", settings.APP_NAME)

    await start_broadcaster()

    scheduler = setup_scheduler()
    scheduler.start()
    logger.info("Scheduler started with %d jobs", len(scheduler.get_jobs()))

    ping_task = asyncio.create_task(manager.start_ping_loop())

    asyncio.create_task(run_initial_fetch())

    yield

    ping_task.cancel()
    try:
        await ping_task
    except asyncio.CancelledError:
        pass

    scheduler.shutdown(wait=False)
    await stop_broadcaster()
    logger.info("%s shut down gracefully", settings.APP_NAME)


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(rest_router)
    app.include_router(ws_router)

    @app.get("/health")
    async def health() -> dict:
        return {
            "status": "ok",
            "ws_connections": manager.active_count,
        }

    return app


app = create_app()
