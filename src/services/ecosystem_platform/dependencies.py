"""
Ecosystem Platform - Dependency Injection
"""

from fastapi import Depends
from infrastructure.database import MongoDB, get_database
from infrastructure.cache import RedisCache, get_cache
from .config import EcosystemSettings
from .services.discovery_service import DiscoveryService
from .services.analytics_service import AnalyticsService


_settings = None
_discovery_service = None
_analytics_service = None


async def get_settings() -> EcosystemSettings:
    """Get service settings"""
    global _settings
    if _settings is None:
        _settings = EcosystemSettings()
    return _settings


async def get_discovery_service(
    db: MongoDB = Depends(get_database),
    cache: RedisCache = Depends(get_cache),
    settings: EcosystemSettings = Depends(get_settings)
) -> DiscoveryService:
    """Get service discovery instance"""
    global _discovery_service
    if _discovery_service is None:
        _discovery_service = DiscoveryService(db, cache, settings)
    return _discovery_service


async def get_analytics_service(
    db: MongoDB = Depends(get_database),
    cache: RedisCache = Depends(get_cache),
    settings: EcosystemSettings = Depends(get_settings)
) -> AnalyticsService:
    """Get analytics service instance"""
    global _analytics_service
    if _analytics_service is None:
        _analytics_service = AnalyticsService(db, cache, settings)
    return _analytics_service
