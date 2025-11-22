"""
APEX System - Configuration Management
Centralized configuration using pydantic-settings
"""

from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables

    All settings can be overridden via environment variables
    Example: APEX_ENVIRONMENT=production
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_prefix="APEX_"
    )

    # Application
    environment: str = Field(default="development", description="Environment: development, staging, production")
    debug: bool = Field(default=False, description="Enable debug mode")
    log_level: str = Field(default="INFO", description="Logging level")
    json_logs: bool = Field(default=True, description="Use JSON formatted logs")

    # Server
    host: str = Field(default="0.0.0.0", description="Server host")
    workers: int = Field(default=1, description="Number of worker processes")

    # MongoDB
    mongodb_url: str = Field(default="mongodb://mongodb:27017", description="MongoDB connection URL")
    mongodb_database: str = Field(default="apex_system", description="MongoDB database name")
    mongodb_min_pool_size: int = Field(default=10, description="MongoDB minimum pool size")
    mongodb_max_pool_size: int = Field(default=100, description="MongoDB maximum pool size")

    # Redis
    redis_url: str = Field(default="redis://redis:6379", description="Redis connection URL")
    redis_db: int = Field(default=0, description="Redis database number")
    redis_password: Optional[str] = Field(default=None, description="Redis password")
    redis_max_connections: int = Field(default=50, description="Redis maximum connections")

    # Security
    secret_key: str = Field(default="your-secret-key-change-in-production", description="Secret key for JWT")
    algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(default=60, description="Access token expiration in minutes")

    # Service Discovery
    ecosystem_platform_url: str = Field(default="http://ecosystem-platform:8002", description="Ecosystem Platform URL")

    # Feature Flags
    enable_metrics: bool = Field(default=True, description="Enable Prometheus metrics")
    enable_tracing: bool = Field(default=False, description="Enable OpenTelemetry tracing")
    enable_caching: bool = Field(default=True, description="Enable Redis caching")

    # Timeouts (seconds)
    http_timeout: int = Field(default=30, description="HTTP request timeout")
    health_check_timeout: int = Field(default=5, description="Health check timeout")
    database_timeout: int = Field(default=10, description="Database operation timeout")

    # Circuit Breaker
    circuit_breaker_failure_threshold: int = Field(default=5, description="Circuit breaker failure threshold")
    circuit_breaker_timeout: int = Field(default=60, description="Circuit breaker timeout in seconds")

    # Rate Limiting
    rate_limit_per_minute: int = Field(default=100, description="Rate limit per minute per IP")

    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.environment == "development"


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance

    Returns:
        Settings instance
    """
    return Settings()
