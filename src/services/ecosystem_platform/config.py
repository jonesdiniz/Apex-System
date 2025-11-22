"""
Ecosystem Platform - Service Configuration
"""

from pydantic import Field
from infrastructure.config import Settings as BaseSettings


class EcosystemSettings(BaseSettings):
    """Ecosystem Platform specific settings"""

    # Service info
    service_name: str = Field(default="ecosystem-platform", env="APEX_SERVICE_NAME")
    service_version: str = Field(default="4.0.0")
    service_port: int = Field(default=8002, env="APEX_SERVICE_PORT")

    # Discovery settings
    discovery_interval: int = Field(default=60, description="Service discovery interval in seconds")
    health_check_timeout: int = Field(default=10, description="Health check timeout in seconds")
    max_concurrent_checks: int = Field(default=5, description="Maximum concurrent health checks")

    # Analytics settings
    analytics_window_hours: int = Field(default=24, description="Analytics data window in hours")
    analytics_retention_hours: int = Field(default=168, description="Analytics retention in hours (7 days)")
    max_metrics_per_service: int = Field(default=1000, description="Maximum metrics stored per service")

    # Cleanup settings
    cleanup_interval: int = Field(default=3600, description="Data cleanup interval in seconds")
