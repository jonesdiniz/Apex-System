"""
APEX System - Event-Driven Architecture
Redis Streams based Event Bus for async communication between services
"""

import asyncio
import json
from typing import Optional, Dict, Any, Callable, List, Awaitable
from datetime import datetime
from redis import asyncio as aioredis
from redis.exceptions import RedisError
from dataclasses import dataclass, asdict
from enum import Enum

from common.logging import get_logger
from common.constants import EventType

logger = get_logger(__name__)


class EventPriority(str, Enum):
    """Event priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Event:
    """
    Event model for inter-service communication

    Attributes:
        event_type: Type of event (from EventType enum)
        source_service: Service that emitted the event
        data: Event payload
        timestamp: When the event was created
        priority: Event priority
        correlation_id: ID to track related events
        metadata: Additional metadata
    """
    event_type: str
    source_service: str
    data: Dict[str, Any]
    timestamp: str = None
    priority: EventPriority = EventPriority.MEDIUM
    correlation_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        result = asdict(self)
        result['priority'] = self.priority.value
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Event':
        """Create Event from dictionary"""
        if 'priority' in data and isinstance(data['priority'], str):
            data['priority'] = EventPriority(data['priority'])
        return cls(**data)


class EventBus:
    """
    Redis Streams based Event Bus

    Provides pub/sub pattern for async communication between microservices.
    Uses Redis Streams for reliability and consumer groups.
    """

    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.redis: Optional[aioredis.Redis] = None
        self.subscribers: Dict[str, List[Callable]] = {}
        self.running = False
        self._consumer_tasks: List[asyncio.Task] = []

    async def connect(self) -> None:
        """Connect to Redis"""
        try:
            self.redis = await aioredis.from_url(
                self.redis_url,
                decode_responses=True,
                encoding='utf-8'
            )
            await self.redis.ping()
            logger.info("Event Bus connected to Redis")
        except RedisError as e:
            logger.error(f"Failed to connect Event Bus to Redis: {e}")
            raise

    async def disconnect(self) -> None:
        """Disconnect from Redis"""
        self.running = False

        # Cancel consumer tasks
        for task in self._consumer_tasks:
            task.cancel()

        if self._consumer_tasks:
            await asyncio.gather(*self._consumer_tasks, return_exceptions=True)

        if self.redis:
            await self.redis.close()
            logger.info("Event Bus disconnected from Redis")

    async def publish(
        self,
        event: Event,
        stream_name: Optional[str] = None
    ) -> bool:
        """
        Publish event to Redis Stream

        Args:
            event: Event to publish
            stream_name: Custom stream name (default: event_type)

        Returns:
            True if published successfully
        """
        if not self.redis:
            logger.error("Event Bus not connected")
            return False

        try:
            stream = stream_name or f"apex:events:{event.event_type}"

            # Serialize event
            event_data = event.to_dict()

            # Convert nested dicts to JSON strings for Redis
            serialized = {
                k: json.dumps(v) if isinstance(v, (dict, list)) else str(v)
                for k, v in event_data.items()
            }

            # Add to stream
            message_id = await self.redis.xadd(stream, serialized)

            logger.info(
                f"Published event",
                extra={
                    "event_type": event.event_type,
                    "source": event.source_service,
                    "stream": stream,
                    "message_id": message_id
                }
            )

            return True

        except RedisError as e:
            logger.error(f"Failed to publish event: {e}", exc_info=True)
            return False

    async def subscribe(
        self,
        event_type: str,
        handler: Callable[[Event], Awaitable[None]],
        consumer_group: str = "apex-consumers",
        consumer_name: Optional[str] = None
    ) -> None:
        """
        Subscribe to events of a specific type

        Args:
            event_type: Event type to subscribe to
            handler: Async function to handle events
            consumer_group: Redis consumer group name
            consumer_name: Unique consumer name
        """
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []

        self.subscribers[event_type].append(handler)

        logger.info(
            f"Subscribed to events",
            extra={"event_type": event_type, "handler": handler.__name__}
        )

    async def start_consuming(
        self,
        consumer_group: str = "apex-consumers",
        consumer_name: Optional[str] = None,
        block_ms: int = 1000
    ) -> None:
        """
        Start consuming events from subscribed streams

        Args:
            consumer_group: Redis consumer group
            consumer_name: Unique consumer name
            block_ms: Block time in milliseconds
        """
        if not self.redis:
            logger.error("Event Bus not connected")
            return

        if not self.subscribers:
            logger.warning("No subscribers registered")
            return

        self.running = True
        consumer_name = consumer_name or f"consumer-{id(self)}"

        # Create consumer groups for each event type
        for event_type in self.subscribers.keys():
            stream = f"apex:events:{event_type}"
            try:
                await self.redis.xgroup_create(
                    stream, consumer_group, id='0', mkstream=True
                )
                logger.info(f"Created consumer group for {stream}")
            except RedisError:
                # Group already exists
                pass

        # Start consumer task for each subscribed event type
        for event_type in self.subscribers.keys():
            task = asyncio.create_task(
                self._consume_stream(
                    event_type, consumer_group, consumer_name, block_ms
                )
            )
            self._consumer_tasks.append(task)

        logger.info(
            f"Started consuming events",
            extra={
                "consumer_group": consumer_group,
                "consumer_name": consumer_name,
                "streams": list(self.subscribers.keys())
            }
        )

    async def _consume_stream(
        self,
        event_type: str,
        consumer_group: str,
        consumer_name: str,
        block_ms: int
    ) -> None:
        """
        Consumer loop for a specific stream

        Args:
            event_type: Event type to consume
            consumer_group: Consumer group name
            consumer_name: Consumer name
            block_ms: Block time
        """
        stream = f"apex:events:{event_type}"

        while self.running:
            try:
                # Read from stream
                messages = await self.redis.xreadgroup(
                    consumer_group,
                    consumer_name,
                    {stream: '>'},
                    count=10,
                    block=block_ms
                )

                if not messages:
                    continue

                # Process messages
                for stream_name, stream_messages in messages:
                    for message_id, message_data in stream_messages:
                        await self._process_message(
                            event_type,
                            message_id,
                            message_data,
                            stream,
                            consumer_group
                        )

            except asyncio.CancelledError:
                logger.info(f"Consumer for {event_type} cancelled")
                break
            except Exception as e:
                logger.error(
                    f"Error consuming stream {stream}: {e}",
                    exc_info=True
                )
                await asyncio.sleep(1)  # Backoff on error

    async def _process_message(
        self,
        event_type: str,
        message_id: str,
        message_data: Dict[str, str],
        stream: str,
        consumer_group: str
    ) -> None:
        """
        Process a single message

        Args:
            event_type: Event type
            message_id: Message ID
            message_data: Message data
            stream: Stream name
            consumer_group: Consumer group
        """
        try:
            # Deserialize event
            event_dict = {}
            for key, value in message_data.items():
                try:
                    # Try to parse JSON
                    event_dict[key] = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    event_dict[key] = value

            event = Event.from_dict(event_dict)

            # Call all handlers for this event type
            handlers = self.subscribers.get(event_type, [])

            for handler in handlers:
                try:
                    await handler(event)
                except Exception as e:
                    logger.error(
                        f"Handler error: {handler.__name__}: {e}",
                        exc_info=True
                    )

            # Acknowledge message
            await self.redis.xack(stream, consumer_group, message_id)

        except Exception as e:
            logger.error(
                f"Failed to process message {message_id}: {e}",
                exc_info=True
            )


# Global event bus instance
_event_bus: Optional[EventBus] = None


async def get_event_bus(redis_url: str = None) -> EventBus:
    """
    Get or create global event bus instance

    Args:
        redis_url: Redis connection URL

    Returns:
        EventBus instance
    """
    global _event_bus

    if _event_bus is None:
        if redis_url is None:
            from infrastructure.config import get_settings
            settings = get_settings()
            redis_url = settings.redis_url

        _event_bus = EventBus(redis_url)
        await _event_bus.connect()

    return _event_bus


async def close_event_bus() -> None:
    """Close global event bus instance"""
    global _event_bus

    if _event_bus:
        await _event_bus.disconnect()
        _event_bus = None
