"""
APEX System - Common Middleware
Shared middleware components for all services
"""

import time
import uuid
from typing import Callable
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from .exceptions import ApexBaseException
from .logging import get_logger

logger = get_logger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Add unique request ID to each request"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id

        return response


class TimingMiddleware(BaseHTTPMiddleware):
    """Add timing information to responses"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()

        response = await call_next(request)

        process_time = (time.time() - start_time) * 1000  # Convert to ms
        response.headers["X-Process-Time"] = f"{process_time:.2f}ms"

        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """Log all requests and responses"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = getattr(request.state, "request_id", "unknown")

        logger.info(
            f"Request started",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "client": request.client.host if request.client else "unknown"
            }
        )

        start_time = time.time()

        try:
            response = await call_next(request)

            duration = (time.time() - start_time) * 1000

            logger.info(
                f"Request completed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": f"{duration:.2f}"
                }
            )

            return response

        except Exception as exc:
            duration = (time.time() - start_time) * 1000

            logger.error(
                f"Request failed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": f"{duration:.2f}",
                    "error": str(exc)
                },
                exc_info=True
            )

            raise


class ExceptionHandlerMiddleware(BaseHTTPMiddleware):
    """Global exception handler"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            return await call_next(request)

        except ApexBaseException as exc:
            # Handle custom APEX exceptions
            return JSONResponse(
                status_code=exc.status_code,
                content=exc.to_dict()
            )

        except ValueError as exc:
            # Handle value errors as validation errors
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": str(exc),
                        "details": {}
                    }
                }
            )

        except Exception as exc:
            # Handle unexpected exceptions
            logger.error(
                f"Unexpected error",
                extra={
                    "path": request.url.path,
                    "error": str(exc)
                },
                exc_info=True
            )

            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": {
                        "code": "INTERNAL_SERVER_ERROR",
                        "message": "An unexpected error occurred",
                        "details": {}
                    }
                }
            )


def setup_middleware(app):
    """
    Setup all common middleware for a FastAPI app

    Args:
        app: FastAPI application instance
    """
    # Add middleware in reverse order (last added = first executed)
    app.add_middleware(ExceptionHandlerMiddleware)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(TimingMiddleware)
    app.add_middleware(RequestIDMiddleware)
