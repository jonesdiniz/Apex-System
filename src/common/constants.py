"""
APEX System - Global Constants
Shared constants and enums for all services
"""

from enum import Enum


class ServiceStatus(str, Enum):
    """Service health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class EventType(str, Enum):
    """Ecosystem event types"""
    SERVICE_HEALTH_CHANGE = "service_health_change"
    RESOURCE_THRESHOLD = "resource_threshold"
    PERFORMANCE_ANOMALY = "performance_anomaly"
    PREDICTION_ALERT = "prediction_alert"
    SCALING_EVENT = "scaling_event"
    SYSTEM_OVERLOAD = "system_overload"
    CUSTOM_EVENT = "custom_event"


class ActionType(str, Enum):
    """Autonomous action types"""
    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"
    RESTART_SERVICE = "restart_service"
    CLEAR_CACHE = "clear_cache"
    OPTIMIZE_CONFIG = "optimize_config"
    REBALANCE_LOAD = "rebalance_load"
    ACTIVATE_CDN = "activate_cdn"
    NOTIFY_OPERATORS = "notify_operators"
    PREVENTIVE_MAINTENANCE = "preventive_maintenance"
    QUARANTINE_CLEAR = "quarantine_clear"


class ConfidenceLevel(str, Enum):
    """Confidence levels for predictions and decisions"""
    LOW = "low"           # < 60%
    MEDIUM = "medium"     # 60-80%
    HIGH = "high"         # 80-95%
    CRITICAL = "critical" # > 95%


class PredictionType(str, Enum):
    """Types of predictions"""
    TRAFFIC_SPIKE = "traffic_spike"
    RESOURCE_SHORTAGE = "resource_shortage"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    SEASONAL_PATTERN = "seasonal_pattern"
    SYSTEM_OVERLOAD = "system_overload"
    ANOMALY_DETECTION = "anomaly_detection"


class CircuitBreakerState(str, Enum):
    """Circuit breaker states"""
    CLOSED = "closed"       # Normal operation
    OPEN = "open"          # Blocking requests
    HALF_OPEN = "half_open" # Testing recovery


# Service Ports (for local execution)
PORTS = {
    "api_gateway": 8000,
    "ecosystem_platform": 8002,
    "creative_studio": 8003,
    "future_casting": 8004,
    "immune_system": 8005,
    "proactive_conversation": 8006,
    "proactive_mitigation": 8007,
    "rl_engine": 8008,
}

# Database Collections/Tables
COLLECTIONS = {
    "services": "services",
    "metrics": "metrics",
    "predictions": "predictions",
    "actions": "actions",
    "events": "events",
    "decisions": "decisions",
    "audit_logs": "audit_logs",
    "tokens": "tokens",
    "cache": "cache",
}

# Cache TTLs (seconds)
CACHE_TTL = {
    "short": 60,        # 1 minute
    "medium": 300,      # 5 minutes
    "long": 3600,       # 1 hour
    "very_long": 86400, # 24 hours
}

# Timeouts (seconds)
TIMEOUTS = {
    "http_request": 30,
    "health_check": 5,
    "database_query": 10,
    "cache_operation": 2,
}

# Thresholds
THRESHOLDS = {
    "cpu_high": 80.0,
    "cpu_low": 30.0,
    "memory_high": 85.0,
    "memory_low": 40.0,
    "response_time_warning": 300,  # ms
    "response_time_critical": 1000, # ms
    "error_rate_warning": 1.0,     # %
    "error_rate_critical": 5.0,    # %
}
