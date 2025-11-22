"""
APEX System - Structured Logging Module
Provides consistent logging across all microservices
"""

import logging
import sys
from typing import Optional
from pythonjsonlogger import jsonlogger


class ApexJsonFormatter(jsonlogger.JsonFormatter):
    """
    Custom JSON formatter for structured logging
    """

    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)

        # Add standard fields
        log_record['service'] = getattr(record, 'service', 'unknown')
        log_record['level'] = record.levelname
        log_record['logger'] = record.name

        # Add exception info if present
        if record.exc_info:
            log_record['exception'] = self.formatException(record.exc_info)


def setup_logging(
    name: str,
    level: str = "INFO",
    service_name: Optional[str] = None,
    json_logs: bool = True
) -> logging.Logger:
    """
    Setup structured logging for a service

    Args:
        name: Logger name (usually __name__)
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        service_name: Name of the service for tracking
        json_logs: Whether to use JSON formatted logs

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers
    logger.handlers = []

    # Create console handler
    handler = logging.StreamHandler(sys.stdout)

    if json_logs:
        # JSON formatter for production
        formatter = ApexJsonFormatter(
            '%(timestamp)s %(level)s %(name)s %(message)s',
            rename_fields={'timestamp': 'asctime'}
        )
    else:
        # Simple formatter for development
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Add service name as extra field
    if service_name:
        logger = logging.LoggerAdapter(logger, {'service': service_name})

    return logger


def get_logger(name: str, service_name: Optional[str] = None) -> logging.Logger:
    """
    Get or create a logger instance

    Args:
        name: Logger name
        service_name: Service name for tracking

    Returns:
        Logger instance
    """
    logger = logging.getLogger(name)

    if service_name and not isinstance(logger, logging.LoggerAdapter):
        logger = logging.LoggerAdapter(logger, {'service': service_name})

    return logger
