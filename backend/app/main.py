import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.images import router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.database.connection import Base, engine
from app.worker.processor import process_queue


# ---------------------------------------------------------------------------
# Configuration & Logging
# ---------------------------------------------------------------------------

settings = get_settings()

configure_logging(settings.log_level)

logger = logging.getLogger("vehicle_pipeline")


# ---------------------------------------------------------------------------
# Application Lifecycle
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup and shutdown lifecycle.

    Startup:
        - Creates database tables if they do not already exist.
        - Starts the asynchronous background processing worker.

    Shutdown:
        - Cancels the background worker cleanly.
    """

    logger.info("Application startup")

    # Initialize database tables.
    Base.metadata.create_all(bind=engine)

    logger.info("Database initialized")

    # Start background processing worker.
    worker = asyncio.create_task(process_queue())

    logger.info("Background processing worker started")

    try:
        yield

    finally:
        logger.info("Application shutdown")

        # Stop background worker gracefully.
        worker.cancel()

        try:
            await worker
        except asyncio.CancelledError:
            pass

        logger.info("Background processing worker stopped")


# ---------------------------------------------------------------------------
# FastAPI Application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Intelligent Vehicle Image Processing Pipeline",
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# API Routes
# ---------------------------------------------------------------------------

app.include_router(router)


# ---------------------------------------------------------------------------
# Health Check
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    """
    Basic health check endpoint.
    """

    return {
        "status": "ok"
    }