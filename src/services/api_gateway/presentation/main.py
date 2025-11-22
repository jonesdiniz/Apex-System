"""
API Gateway - FastAPI Application
Entry point for the API Gateway service
"""

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from common.logging import setup_logging
from common.middleware import setup_middleware
from common.health import HealthRouter
from infrastructure import get_database, close_database, get_cache, close_cache
from common.event_bus import get_event_bus, close_event_bus
from .routers import auth_router

# Setup logging
logger = setup_logging(__name__, service_name="api-gateway")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager

    Handles startup and shutdown events
    """
    # Startup
    logger.info("API Gateway starting up...")

    # Connect to infrastructure
    try:
        db = await get_database()
        logger.info(f"Connected to MongoDB: {db.db.name if db.db else 'N/A'}")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}", exc_info=True)

    try:
        cache = await get_cache()
        logger.info("Connected to Redis cache")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}", exc_info=True)

    try:
        event_bus = await get_event_bus()
        logger.info("Connected to Event Bus (Redis Streams)")
    except Exception as e:
        logger.error(f"Failed to connect to Event Bus: {e}", exc_info=True)

    logger.info("✅ API Gateway started successfully")

    yield

    # Shutdown
    logger.info("API Gateway shutting down...")

    await close_event_bus()
    await close_cache()
    await close_database()

    logger.info("✅ API Gateway shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="API Gateway",
    description="Intelligent API Gateway with OAuth 2.0, Event-Driven Architecture, and Clean Architecture",
    version="4.0.0",
    lifespan=lifespan
)

# Setup middleware
setup_middleware(app)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics
Instrumentator().instrument(app).expose(app)

# Health check router
health_router = HealthRouter(
    service_name="api-gateway",
    version="4.0.0",
)
app.include_router(health_router.router)

# Business routers
app.include_router(auth_router)

# Root endpoint
@app.get("/")
async def root():
    """API Gateway information"""
    return {
        "service": "api-gateway",
        "version": "4.0.0",
        "description": "Intelligent API Gateway with OAuth 2.0",
        "architecture": "Clean Architecture + Event-Driven",
        "features": [
            "OAuth 2.0 (5 platforms)",
            "Event Bus (Redis Streams)",
            "MongoDB persistence",
            "Health checks",
            "Prometheus metrics"
        ],
        "platforms": ["google", "linkedin", "meta", "twitter", "tiktok"]
    }


# Run with uvicorn
if __name__ == "__main__":
    import uvicorn
    from infrastructure.config import get_settings

    settings = get_settings()
    port = getattr(settings, 'service_port', 8000)

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )
