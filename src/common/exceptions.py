"""
APEX System - Custom Exceptions
Standardized exception hierarchy for all services
"""

from typing import Optional, Dict, Any


class ApexBaseException(Exception):
    """Base exception for all APEX system errors"""

    def __init__(
        self,
        message: str,
        code: str = "APEX_ERROR",
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 500
    ):
        self.message = message
        self.code = code
        self.details = details or {}
        self.status_code = status_code
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses"""
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details
            }
        }


class ValidationError(ApexBaseException):
    """Validation error (400)"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            details=details,
            status_code=400
        )


class NotFoundError(ApexBaseException):
    """Resource not found error (404)"""

    def __init__(self, resource: str, identifier: str):
        super().__init__(
            message=f"{resource} not found: {identifier}",
            code="NOT_FOUND",
            details={"resource": resource, "identifier": identifier},
            status_code=404
        )


class UnauthorizedError(ApexBaseException):
    """Unauthorized access error (401)"""

    def __init__(self, message: str = "Unauthorized access"):
        super().__init__(
            message=message,
            code="UNAUTHORIZED",
            status_code=401
        )


class ForbiddenError(ApexBaseException):
    """Forbidden access error (403)"""

    def __init__(self, message: str = "Access forbidden"):
        super().__init__(
            message=message,
            code="FORBIDDEN",
            status_code=403
        )


class ServiceUnavailableError(ApexBaseException):
    """Service unavailable error (503)"""

    def __init__(self, service_name: str, reason: Optional[str] = None):
        message = f"Service {service_name} is unavailable"
        if reason:
            message += f": {reason}"

        super().__init__(
            message=message,
            code="SERVICE_UNAVAILABLE",
            details={"service": service_name, "reason": reason},
            status_code=503
        )


class CircuitBreakerOpenError(ApexBaseException):
    """Circuit breaker is open (503)"""

    def __init__(self, service_name: str):
        super().__init__(
            message=f"Circuit breaker open for {service_name}",
            code="CIRCUIT_BREAKER_OPEN",
            details={"service": service_name},
            status_code=503
        )


class DatabaseError(ApexBaseException):
    """Database operation error (500)"""

    def __init__(self, operation: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"Database error during {operation}",
            code="DATABASE_ERROR",
            details=details,
            status_code=500
        )


class ExternalServiceError(ApexBaseException):
    """External service communication error (502)"""

    def __init__(self, service_name: str, reason: str):
        super().__init__(
            message=f"Error communicating with {service_name}: {reason}",
            code="EXTERNAL_SERVICE_ERROR",
            details={"service": service_name, "reason": reason},
            status_code=502
        )
