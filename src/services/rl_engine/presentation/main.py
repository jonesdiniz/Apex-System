"""
RL Engine - FastAPI Application
Entry point for the RL Engine service with Clean Architecture + Event-Driven
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
from infrastructure.config import get_settings
from .routers import actions_router, learning_router
from .dependencies import (
    get_rl_service,
    get_event_handlers,
    initialize_event_subscriptions,
    cleanup_resources
)


# Setup logging
logger = setup_logging(__name__, service_name="rl-engine")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager

    Handles startup and shutdown events with proper initialization order
    """
    # Startup
    logger.info("RL Engine starting up...")

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
        settings = get_settings()
        if settings.event_bus_enabled:
            event_bus = await get_event_bus()
            logger.info("Connected to Event Bus (Redis Streams)")
        else:
            logger.info("Event Bus disabled")
    except Exception as e:
        logger.error(f"Failed to connect to Event Bus: {e}", exc_info=True)

    # Initialize RL Service (loads strategies and Q-table from MongoDB)
    try:
        rl_service = await get_rl_service()
        logger.info("RL Service initialized with loaded strategies")
    except Exception as e:
        logger.error(f"Failed to initialize RL Service: {e}", exc_info=True)

    # Initialize event subscriptions for event-driven learning
    try:
        settings = get_settings()
        if settings.event_bus_enabled:
            await initialize_event_subscriptions()
            logger.info("✅ Event subscriptions initialized - Event-Driven Learning active")
        else:
            logger.info("Event subscriptions disabled - HTTP-only mode")
    except Exception as e:
        logger.error(f"Failed to initialize event subscriptions: {e}", exc_info=True)

    logger.info("✅ RL Engine started successfully")

    yield

    # Shutdown
    logger.info("RL Engine shutting down...")

    # Save current state
    try:
        await cleanup_resources()
        logger.info("Saved RL Engine state")
    except Exception as e:
        logger.error(f"Failed to save RL Engine state: {e}", exc_info=True)

    await close_event_bus()
    await close_cache()
    await close_database()

    logger.info("✅ RL Engine shutdown complete")


# Create FastAPI app
settings = get_settings()

app = FastAPI(
    title="RL Engine",
    description="Intelligent RL Engine with Q-Learning, Dual Buffer, Event-Driven Learning, and Clean Architecture",
    version=settings.version,
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
    service_name=settings.service_name,
    version=settings.version,
)
app.include_router(health_router.router)

# Business routers
app.include_router(actions_router)
app.include_router(learning_router)


# Root endpoint
@app.get("/")
async def root():
    """RL Engine information"""
    settings = get_settings()

    return {
        "service": "rl-engine",
        "version": settings.version,
        "description": "Intelligent RL Engine with Q-Learning",
        "architecture": "Clean Architecture + Event-Driven + Dual Buffer",
        "features": [
            "Q-Learning Algorithm",
            "Dual Buffer (Active + History)",
            "Event-Driven Learning",
            "MongoDB persistence",
            "Event Bus (Redis Streams)",
            "Health checks",
            "Prometheus metrics",
            "12 campaign optimization actions"
        ],
        "algorithm": {
            "type": "Q-Learning",
            "learning_rate": settings.learning_rate,
            "discount_factor": settings.discount_factor,
            "exploration_rate": settings.exploration_rate
        },
        "dual_buffer": {
            "max_active_buffer": settings.max_active_buffer,
            "max_history_buffer": settings.max_history_buffer,
            "auto_process_threshold": settings.auto_process_threshold,
            "history_retention_hours": settings.history_retention_hours
        },
        "event_driven": {
            "enabled": settings.event_bus_enabled,
            "subscribed_events": [
                "traffic.request_completed",
                "campaign.performance_updated",
                "rl.strategy_feedback"
            ] if settings.event_bus_enabled else []
        },
        "endpoints": {
            "generate_action": "/api/v1/actions/generate",
            "learn": "/api/v1/learn",
            "strategies": "/api/v1/strategies",
            "metrics": "/api/v1/metrics",
            "active_buffer": "/api/v1/buffer/active",
            "history_buffer": "/api/v1/buffer/history",
            "force_process": "/api/v1/force_process",
            "config": "/api/v1/config",
            "health": "/health"
        }
    }


# Run with uvicorn
if __name__ == "__main__":
    import uvicorn

    port = settings.service_port

    uvicorn.run(
        "main:app",
        host=settings.service_host,
        port=port,
        reload=True,
        log_level=settings.log_level.lower()
    )
