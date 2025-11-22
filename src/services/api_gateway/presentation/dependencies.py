"""
API Gateway - Dependency Injection
FastAPI dependency providers
"""

from fastapi import Depends

from infrastructure.database import MongoDB, get_database
from common.event_bus import EventBus, get_event_bus
from ..infrastructure.repositories import MongoOAuthRepository
from ..infrastructure.oauth_providers import OAuthConfigProvider
from ..application.oauth_service import OAuthService


# Global instances (singletons)
_oauth_config_provider = None
_oauth_service = None


async def get_oauth_repository(
    db: MongoDB = Depends(get_database)
) -> MongoOAuthRepository:
    """Get OAuth repository instance"""
    return MongoOAuthRepository(db)


async def get_oauth_config_provider() -> OAuthConfigProvider:
    """Get OAuth config provider instance"""
    global _oauth_config_provider
    if _oauth_config_provider is None:
        _oauth_config_provider = OAuthConfigProvider()
    return _oauth_config_provider


async def get_oauth_service(
    oauth_repository: MongoOAuthRepository = Depends(get_oauth_repository),
    oauth_config_provider: OAuthConfigProvider = Depends(get_oauth_config_provider),
    event_bus: EventBus = Depends(get_event_bus)
) -> OAuthService:
    """
    Get OAuth service instance

    Dependency injection of:
    - OAuth repository (MongoDB)
    - OAuth config provider (env vars)
    - Event bus (Redis Streams)
    """
    global _oauth_service
    if _oauth_service is None:
        _oauth_service = OAuthService(
            oauth_repository=oauth_repository,
            oauth_config_provider=oauth_config_provider,
            event_bus=event_bus
        )
    return _oauth_service
