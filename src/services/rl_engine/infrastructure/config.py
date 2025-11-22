"""
RL Engine - Infrastructure Layer - Configuration
Environment-based configuration for local execution
"""

from pydantic_settings import BaseSettings
from pydantic import Field


class RLEngineSettings(BaseSettings):
    """RL Engine Configuration Settings"""

    # Service Configuration
    service_name: str = Field(default="rl-engine", env="SERVICE_NAME")
    service_port: int = Field(default=8001, env="PORT")
    service_host: str = Field(default="0.0.0.0", env="HOST")
    environment: str = Field(default="development", env="ENVIRONMENT")
    version: str = Field(default="4.0.0", env="VERSION")

    # Q-Learning Hyperparameters
    learning_rate: float = Field(default=0.1, env="LEARNING_RATE")
    discount_factor: float = Field(default=0.95, env="DISCOUNT_FACTOR")
    exploration_rate: float = Field(default=0.15, env="EXPLORATION_RATE")
    confidence_threshold: float = Field(default=0.7, env="CONFIDENCE_THRESHOLD")
    min_experiences_for_learning: int = Field(default=10, env="MIN_EXPERIENCES_FOR_LEARNING")

    # Dual Buffer Configuration
    max_active_buffer: int = Field(default=25, env="MAX_ACTIVE_BUFFER")
    max_history_buffer: int = Field(default=1000, env="MAX_HISTORY_BUFFER")
    auto_process_threshold: int = Field(default=15, env="AUTO_PROCESS_THRESHOLD")
    history_retention_hours: int = Field(default=72, env="HISTORY_RETENTION_HOURS")

    # Performance Configuration
    batch_processing_size: int = Field(default=25, env="BATCH_PROCESSING_SIZE")
    auto_save_interval: int = Field(default=180, env="AUTO_SAVE_INTERVAL")  # 3 minutes
    memory_cleanup_interval: int = Field(default=1800, env="MEMORY_CLEANUP_INTERVAL")  # 30 min

    # MongoDB Configuration
    mongodb_url: str = Field(default="mongodb://localhost:27017", env="MONGODB_URL")
    mongodb_db_name: str = Field(default="apex_system", env="MONGODB_DB_NAME")

    # Redis Configuration
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    redis_event_stream: str = Field(default="apex:events:rl", env="REDIS_EVENT_STREAM")

    # Event Bus Configuration
    event_bus_enabled: bool = Field(default=True, env="EVENT_BUS_ENABLED")
    event_consumer_group: str = Field(default="rl-engine-group", env="EVENT_CONSUMER_GROUP")

    # Logging Configuration
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    enable_structured_logging: bool = Field(default=True, env="ENABLE_STRUCTURED_LOGGING")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Singleton instance
_settings: RLEngineSettings = None


def get_settings() -> RLEngineSettings:
    """Get settings singleton"""
    global _settings
    if _settings is None:
        _settings = RLEngineSettings()
    return _settings
