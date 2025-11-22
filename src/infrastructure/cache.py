"""
APEX System - Redis Cache Client
Distributed cache for all services
"""

import json
import pickle
from typing import Optional, Any
from datetime import timedelta
from redis import asyncio as aioredis
from redis.exceptions import RedisError
from common.logging import get_logger
from common.exceptions import DatabaseError
from .config import get_settings

logger = get_logger(__name__)


class RedisCache:
    """
    Redis cache client with async support

    Provides distributed caching across all services
    """

    def __init__(self):
        self.client: Optional[aioredis.Redis] = None
        self._connected = False
        self.settings = get_settings()

    async def connect(self) -> None:
        """Connect to Redis"""
        if self._connected:
            logger.warning("Redis already connected")
            return

        try:
            self.client = await aioredis.from_url(
                self.settings.redis_url,
                db=self.settings.redis_db,
                password=self.settings.redis_password,
                max_connections=self.settings.redis_max_connections,
                decode_responses=False,  # We'll handle encoding
                socket_connect_timeout=5,
            )

            # Test connection
            await self.client.ping()
            self._connected = True

            logger.info(
                f"Connected to Redis",
                extra={
                    "db": self.settings.redis_db,
                    "url": self.settings.redis_url.split('@')[-1]
                }
            )

        except RedisError as e:
            logger.error(f"Failed to connect to Redis: {e}", exc_info=True)
            raise DatabaseError("connect", {"error": str(e)})

    async def disconnect(self) -> None:
        """Disconnect from Redis"""
        if not self._connected:
            return

        if self.client:
            await self.client.close()
            self._connected = False
            logger.info("Disconnected from Redis")

    async def health_check(self) -> str:
        """
        Check Redis health

        Returns:
            Status string: "healthy", "unhealthy"
        """
        try:
            if not self._connected:
                return "disconnected"

            await self.client.ping()
            return "healthy"

        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return "unhealthy"

    async def get(self, key: str, deserialize: bool = True) -> Optional[Any]:
        """
        Get value from cache

        Args:
            key: Cache key
            deserialize: Whether to deserialize the value

        Returns:
            Cached value or None if not found
        """
        if not self._connected:
            logger.warning("Cache not connected, returning None")
            return None

        try:
            value = await self.client.get(key)

            if value is None:
                return None

            if deserialize:
                try:
                    # Try JSON first
                    return json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    # Fall back to pickle
                    try:
                        return pickle.loads(value)
                    except Exception:
                        return value.decode() if isinstance(value, bytes) else value

            return value

        except RedisError as e:
            logger.error(f"Cache get failed for key {key}: {e}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        serialize: bool = True
    ) -> bool:
        """
        Set value in cache

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            serialize: Whether to serialize the value

        Returns:
            True if successful
        """
        if not self._connected:
            logger.warning("Cache not connected, skipping set")
            return False

        try:
            if serialize:
                try:
                    # Try JSON first (more portable)
                    serialized_value = json.dumps(value)
                except (TypeError, ValueError):
                    # Fall back to pickle
                    serialized_value = pickle.dumps(value)
            else:
                serialized_value = value

            if ttl:
                await self.client.setex(key, ttl, serialized_value)
            else:
                await self.client.set(key, serialized_value)

            return True

        except RedisError as e:
            logger.error(f"Cache set failed for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """
        Delete key from cache

        Args:
            key: Cache key

        Returns:
            True if key was deleted
        """
        if not self._connected:
            return False

        try:
            result = await self.client.delete(key)
            return result > 0

        except RedisError as e:
            logger.error(f"Cache delete failed for key {key}: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """
        Check if key exists

        Args:
            key: Cache key

        Returns:
            True if key exists
        """
        if not self._connected:
            return False

        try:
            result = await self.client.exists(key)
            return result > 0

        except RedisError as e:
            logger.error(f"Cache exists check failed for key {key}: {e}")
            return False

    async def expire(self, key: str, ttl: int) -> bool:
        """
        Set expiration on key

        Args:
            key: Cache key
            ttl: Time to live in seconds

        Returns:
            True if expiration was set
        """
        if not self._connected:
            return False

        try:
            return await self.client.expire(key, ttl)

        except RedisError as e:
            logger.error(f"Cache expire failed for key {key}: {e}")
            return False

    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """
        Increment counter

        Args:
            key: Cache key
            amount: Amount to increment

        Returns:
            New value or None on error
        """
        if not self._connected:
            return None

        try:
            return await self.client.incrby(key, amount)

        except RedisError as e:
            logger.error(f"Cache increment failed for key {key}: {e}")
            return None

    async def get_many(self, keys: list[str]) -> dict[str, Any]:
        """
        Get multiple values

        Args:
            keys: List of cache keys

        Returns:
            Dictionary of key-value pairs
        """
        if not self._connected or not keys:
            return {}

        try:
            values = await self.client.mget(keys)
            result = {}

            for key, value in zip(keys, values):
                if value is not None:
                    try:
                        result[key] = json.loads(value)
                    except (json.JSONDecodeError, TypeError):
                        try:
                            result[key] = pickle.loads(value)
                        except Exception:
                            result[key] = value.decode() if isinstance(value, bytes) else value

            return result

        except RedisError as e:
            logger.error(f"Cache get_many failed: {e}")
            return {}

    async def set_many(
        self,
        mapping: dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set multiple values

        Args:
            mapping: Dictionary of key-value pairs
            ttl: Time to live in seconds (applied to all keys)

        Returns:
            True if successful
        """
        if not self._connected or not mapping:
            return False

        try:
            # Serialize all values
            serialized = {}
            for key, value in mapping.items():
                try:
                    serialized[key] = json.dumps(value)
                except (TypeError, ValueError):
                    serialized[key] = pickle.dumps(value)

            # Set all values
            await self.client.mset(serialized)

            # Set TTL if specified
            if ttl:
                pipeline = self.client.pipeline()
                for key in serialized.keys():
                    pipeline.expire(key, ttl)
                await pipeline.execute()

            return True

        except RedisError as e:
            logger.error(f"Cache set_many failed: {e}")
            return False

    async def clear_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching pattern

        Args:
            pattern: Key pattern (e.g., "user:*")

        Returns:
            Number of keys deleted
        """
        if not self._connected:
            return 0

        try:
            keys = []
            async for key in self.client.scan_iter(match=pattern):
                keys.append(key)

            if keys:
                return await self.client.delete(*keys)

            return 0

        except RedisError as e:
            logger.error(f"Cache clear_pattern failed for pattern {pattern}: {e}")
            return 0


# Global cache instance
_cache_instance: Optional[RedisCache] = None


async def get_cache() -> RedisCache:
    """
    Get or create global cache instance

    Returns:
        RedisCache instance
    """
    global _cache_instance

    if _cache_instance is None:
        _cache_instance = RedisCache()
        await _cache_instance.connect()

    return _cache_instance


async def close_cache() -> None:
    """Close global cache instance"""
    global _cache_instance

    if _cache_instance:
        await _cache_instance.disconnect()
        _cache_instance = None
