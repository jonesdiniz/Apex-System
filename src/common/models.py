"""
APEX System - Shared Data Models
Base models and schemas used across all services
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict


class BaseApexModel(BaseModel):
    """Base model with common configuration"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {}
        },
        populate_by_name=True,
        from_attributes=True
    )


class ServiceInfo(BaseApexModel):
    """Service information model"""
    name: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    port: int = Field(..., description="Service port")
    url: str = Field(..., description="Service URL")
    status: str = Field(..., description="Service status")
    last_check: datetime = Field(default_factory=datetime.utcnow)
    response_time_ms: float = Field(0.0, description="Response time in milliseconds")


class ServiceMetrics(BaseApexModel):
    """Comprehensive service metrics"""
    service_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Performance metrics
    cpu_usage: float = Field(0.0, ge=0, le=100, description="CPU usage percentage")
    memory_usage: float = Field(0.0, ge=0, le=100, description="Memory usage percentage")
    disk_usage: float = Field(0.0, ge=0, le=100, description="Disk usage percentage")

    # Request metrics
    total_requests: int = Field(0, ge=0)
    successful_requests: int = Field(0, ge=0)
    failed_requests: int = Field(0, ge=0)
    avg_response_time: float = Field(0.0, ge=0, description="Average response time in ms")
    min_response_time: float = Field(0.0, ge=0)
    max_response_time: float = Field(0.0, ge=0)

    # Health metrics
    health_score: float = Field(100.0, ge=0, le=100, description="Overall health score")
    uptime_percentage: float = Field(100.0, ge=0, le=100)
    error_rate: float = Field(0.0, ge=0, le=100, description="Error rate percentage")

    # Additional data
    active_connections: int = Field(0, ge=0)
    quarantine_level: int = Field(0, ge=0, le=100)
    cache_hit_rate: Optional[float] = Field(None, ge=0, le=100)

    @property
    def is_healthy(self) -> bool:
        """Check if service is healthy"""
        return (
            self.health_score >= 70 and
            self.cpu_usage < 90 and
            self.memory_usage < 90 and
            self.error_rate < 5.0
        )


class HealthCheckResponse(BaseApexModel):
    """Standard health check response"""
    status: str = Field(..., description="Health status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    uptime_seconds: float = Field(0.0, ge=0)
    details: Optional[Dict[str, Any]] = None


class DeepHealthCheckResponse(HealthCheckResponse):
    """Deep health check with dependencies"""
    dependencies: Dict[str, str] = Field(default_factory=dict)
    metrics: Optional[ServiceMetrics] = None
    database_status: str = "unknown"
    cache_status: str = "unknown"


class AutonomousAction(BaseApexModel):
    """Autonomous action executed by the system"""
    action_id: str
    action_type: str
    service_name: str
    triggered_by: str
    triggered_at: datetime = Field(default_factory=datetime.utcnow)
    executed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: str = "pending"  # pending, executing, completed, failed
    confidence: float = Field(..., ge=0, le=1)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class Prediction(BaseApexModel):
    """Prediction model"""
    prediction_id: str
    prediction_type: str
    service_name: str
    predicted_at: datetime = Field(default_factory=datetime.utcnow)
    predicted_for: datetime  # When the prediction is for
    confidence: float = Field(..., ge=0, le=1)
    metric_name: str
    current_value: float
    predicted_value: float
    threshold: Optional[float] = None
    severity: str  # low, medium, high, critical
    recommended_actions: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EcosystemEvent(BaseApexModel):
    """Ecosystem event"""
    event_id: str
    event_type: str
    service_name: str
    occurred_at: datetime = Field(default_factory=datetime.utcnow)
    severity: str
    description: str
    metrics: Optional[Dict[str, Any]] = None
    triggered_actions: List[str] = Field(default_factory=list)


class AuditLog(BaseApexModel):
    """Audit log entry"""
    log_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    service_name: str
    action: str
    actor: str  # system, user, service
    details: Dict[str, Any] = Field(default_factory=dict)
    success: bool
    error_message: Optional[str] = None


class CacheEntry(BaseApexModel):
    """Cache entry model"""
    key: str
    value: Any
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    ttl: Optional[int] = None  # seconds
    hit_count: int = 0
