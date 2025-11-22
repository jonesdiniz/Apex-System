"""
APEX System - Common Module
Shared utilities and components for all microservices
"""

__version__ = "4.0.0"
__author__ = "APEX Team"

from .logging import setup_logging, get_logger
from .exceptions import (
    ApexBaseException,
    ValidationError,
    NotFoundError,
    UnauthorizedError,
    ServiceUnavailableError,
)
from .constants import (
    ServiceStatus,
    EventType,
    ActionType,
    ConfidenceLevel,
)

__all__ = [
    "setup_logging",
    "get_logger",
    "ApexBaseException",
    "ValidationError",
    "NotFoundError",
    "UnauthorizedError",
    "ServiceUnavailableError",
    "ServiceStatus",
    "EventType",
    "ActionType",
    "ConfidenceLevel",
]
