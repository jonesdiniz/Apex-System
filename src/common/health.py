"""
APEX System - Health Check Router
Standardized health check endpoints for all services
"""

import time
from datetime import datetime
from typing import Optional, Dict, Any, Callable
from fastapi import APIRouter, Depends
from .models import HealthCheckResponse, DeepHealthCheckResponse


class HealthRouter:
    """
    Reusable health check router for all services

    Usage:
        health_router = HealthRouter(
            service_name="my-service",
            version="1.0.0",
            get_metrics_func=get_my_metrics
        )
        app.include_router(health_router.router)
    """

    def __init__(
        self,
        service_name: str,
        version: str,
        get_metrics_func: Optional[Callable] = None,
        check_dependencies_func: Optional[Callable] = None,
        check_database_func: Optional[Callable] = None,
        check_cache_func: Optional[Callable] = None,
    ):
        self.service_name = service_name
        self.version = version
        self.start_time = time.time()
        self.get_metrics_func = get_metrics_func
        self.check_dependencies_func = check_dependencies_func
        self.check_database_func = check_database_func
        self.check_cache_func = check_cache_func

        self.router = APIRouter(tags=["health"])
        self._setup_routes()

    def _setup_routes(self):
        """Setup health check routes"""

        @self.router.get("/health", response_model=HealthCheckResponse)
        async def health_check():
            """Basic health check endpoint"""
            return HealthCheckResponse(
                status="healthy",
                service=self.service_name,
                version=self.version,
                uptime_seconds=time.time() - self.start_time
            )

        @self.router.get("/health/deep", response_model=DeepHealthCheckResponse)
        async def deep_health_check():
            """Deep health check with dependencies"""
            uptime = time.time() - self.start_time

            # Get metrics if available
            metrics = None
            if self.get_metrics_func:
                try:
                    metrics = await self.get_metrics_func() if callable(self.get_metrics_func) else None
                except Exception:
                    pass

            # Check dependencies
            dependencies = {}
            if self.check_dependencies_func:
                try:
                    dependencies = await self.check_dependencies_func() if callable(self.check_dependencies_func) else {}
                except Exception:
                    dependencies = {"error": "failed to check dependencies"}

            # Check database
            database_status = "unknown"
            if self.check_database_func:
                try:
                    database_status = await self.check_database_func() if callable(self.check_database_func) else "unknown"
                except Exception:
                    database_status = "error"

            # Check cache
            cache_status = "unknown"
            if self.check_cache_func:
                try:
                    cache_status = await self.check_cache_func() if callable(self.check_cache_func) else "unknown"
                except Exception:
                    cache_status = "error"

            # Determine overall status
            status = "healthy"
            if database_status == "error" or cache_status == "error":
                status = "degraded"
            if metrics and hasattr(metrics, 'is_healthy') and not metrics.is_healthy:
                status = "degraded"

            return DeepHealthCheckResponse(
                status=status,
                service=self.service_name,
                version=self.version,
                uptime_seconds=uptime,
                dependencies=dependencies,
                metrics=metrics,
                database_status=database_status,
                cache_status=cache_status
            )

        @self.router.get("/ready")
        async def readiness_check():
            """Kubernetes readiness probe"""
            # Check if service is ready to accept traffic
            ready = True

            # Check database connection
            if self.check_database_func:
                try:
                    db_status = await self.check_database_func() if callable(self.check_database_func) else "unknown"
                    ready = ready and db_status in ["healthy", "connected"]
                except Exception:
                    ready = False

            return {
                "status": "ready" if ready else "not_ready",
                "service": self.service_name
            }

        @self.router.get("/live")
        async def liveness_check():
            """Kubernetes liveness probe"""
            # Basic check that service is alive
            return {
                "status": "alive",
                "service": self.service_name,
                "timestamp": datetime.utcnow().isoformat()
            }
