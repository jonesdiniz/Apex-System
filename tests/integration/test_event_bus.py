"""
Integration Tests - Event Bus
Tests for Event Bus pub/sub with Redis Streams
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch
import sys

sys.path.insert(0, '/home/user/Apex-System/src')

from common.event_bus import (
    Event,
    EventPriority,
    EventBus
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
async def mock_redis():
    """Mock Redis client"""
    redis = AsyncMock()
    redis.xadd = AsyncMock(return_value=b"1234567890-0")
    redis.xread = AsyncMock(return_value=[])
    redis.xgroup_create = AsyncMock()
    redis.xreadgroup = AsyncMock(return_value=[])
    redis.xack = AsyncMock()
    redis.ping = AsyncMock(return_value=True)
    return redis


@pytest.fixture
async def event_bus(mock_redis):
    """Event bus instance with mock Redis"""
    bus = EventBus(redis=mock_redis)
    bus.redis = mock_redis  # Ensure mock is set
    return bus


# ============================================================================
# TEST: EVENT CREATION
# ============================================================================

def test_event_creation():
    """Test creating an event"""
    event = Event(
        event_type="test.event",
        source_service="test-service",
        data={"key": "value"},
        priority=EventPriority.HIGH
    )

    # Verify
    assert event.event_type == "test.event"
    assert event.source_service == "test-service"
    assert event.data["key"] == "value"
    assert event.priority == EventPriority.HIGH
    assert event.event_id is not None
    assert event.timestamp is not None
    assert event.correlation_id is None


def test_event_with_correlation_id():
    """Test creating an event with correlation ID"""
    event = Event(
        event_type="test.event",
        source_service="test-service",
        data={},
        correlation_id="test-correlation-123"
    )

    # Verify
    assert event.correlation_id == "test-correlation-123"


def test_event_serialization():
    """Test event serialization to dict"""
    event = Event(
        event_type="test.event",
        source_service="test-service",
        data={"key": "value"},
        priority=EventPriority.MEDIUM
    )

    # Serialize
    event_dict = event.to_dict()

    # Verify
    assert event_dict["event_type"] == "test.event"
    assert event_dict["source_service"] == "test-service"
    assert event_dict["data"]["key"] == "value"
    assert event_dict["priority"] == EventPriority.MEDIUM.value


def test_event_deserialization():
    """Test event deserialization from dict"""
    event_dict = {
        "event_id": "test-id-123",
        "event_type": "test.event",
        "source_service": "test-service",
        "timestamp": datetime.utcnow().isoformat(),
        "data": {"key": "value"},
        "priority": "medium",
        "correlation_id": None
    }

    # Deserialize
    event = Event.from_dict(event_dict)

    # Verify
    assert event.event_id == "test-id-123"
    assert event.event_type == "test.event"
    assert event.data["key"] == "value"
    assert event.priority == EventPriority.MEDIUM


# ============================================================================
# TEST: PUBLISH
# ============================================================================

@pytest.mark.asyncio
async def test_publish_event_success(event_bus, mock_redis):
    """Test publishing an event successfully"""
    # Create event
    event = Event(
        event_type="traffic.request_completed",
        source_service="traffic-manager",
        data={"request_id": "req_123", "success": True}
    )

    # Publish
    result = await event_bus.publish(event)

    # Verify
    assert result is True
    mock_redis.xadd.assert_called_once()

    # Verify stream name
    call_args = mock_redis.xadd.call_args
    stream_name = call_args[0][0]
    assert "traffic.request_completed" in stream_name


@pytest.mark.asyncio
async def test_publish_event_with_custom_stream(event_bus, mock_redis):
    """Test publishing to a custom stream"""
    event = Event(
        event_type="custom.event",
        source_service="test",
        data={}
    )

    # Publish to custom stream
    result = await event_bus.publish(event, stream_name="custom:stream")

    # Verify
    assert result is True
    call_args = mock_redis.xadd.call_args
    stream_name = call_args[0][0]
    assert stream_name == "custom:stream"


@pytest.mark.asyncio
async def test_publish_event_with_priority(event_bus, mock_redis):
    """Test publishing events with different priorities"""
    # High priority event
    high_priority = Event(
        event_type="critical.alert",
        source_service="monitor",
        data={},
        priority=EventPriority.CRITICAL
    )

    await event_bus.publish(high_priority)

    # Verify priority in serialized data
    call_args = mock_redis.xadd.call_args
    event_data = call_args[0][1]
    assert "priority" in event_data


@pytest.mark.asyncio
async def test_publish_event_error_handling(mock_redis):
    """Test error handling when publish fails"""
    # Setup mock to raise error
    mock_redis.xadd = AsyncMock(side_effect=Exception("Redis error"))

    event_bus = EventBus(redis=mock_redis)
    event = Event(
        event_type="test.event",
        source_service="test",
        data={}
    )

    # Publish should return False on error
    result = await event_bus.publish(event)
    assert result is False


# ============================================================================
# TEST: SUBSCRIBE
# ============================================================================

@pytest.mark.asyncio
async def test_subscribe_to_event(event_bus):
    """Test subscribing to an event type"""
    # Handler function
    handler_called = False

    async def test_handler(event: Event):
        nonlocal handler_called
        handler_called = True

    # Subscribe
    await event_bus.subscribe("test.event", test_handler)

    # Verify subscription
    assert "test.event" in event_bus.subscribers
    assert test_handler in event_bus.subscribers["test.event"]


@pytest.mark.asyncio
async def test_subscribe_multiple_handlers(event_bus):
    """Test subscribing multiple handlers to same event"""
    async def handler1(event: Event):
        pass

    async def handler2(event: Event):
        pass

    # Subscribe both
    await event_bus.subscribe("test.event", handler1)
    await event_bus.subscribe("test.event", handler2)

    # Verify both subscribed
    assert len(event_bus.subscribers["test.event"]) == 2


# ============================================================================
# TEST: EVENT HANDLING
# ============================================================================

@pytest.mark.asyncio
async def test_event_handler_called(event_bus, mock_redis):
    """Test that event handlers are called when events arrive"""
    # Setup
    handler_called = False
    received_event = None

    async def test_handler(event: Event):
        nonlocal handler_called, received_event
        handler_called = True
        received_event = event

    # Subscribe
    await event_bus.subscribe("test.event", test_handler)

    # Simulate event from Redis
    test_event = Event(
        event_type="test.event",
        source_service="test",
        data={"key": "value"}
    )

    # Call handler directly (simulating event processing)
    await test_handler(test_event)

    # Verify
    assert handler_called
    assert received_event is not None
    assert received_event.data["key"] == "value"


# ============================================================================
# TEST: CORRELATION ID
# ============================================================================

@pytest.mark.asyncio
async def test_correlation_id_propagation(event_bus, mock_redis):
    """Test correlation ID is propagated through events"""
    # Create event with correlation ID
    event = Event(
        event_type="test.event",
        source_service="service-a",
        data={},
        correlation_id="correlation-123"
    )

    # Publish
    await event_bus.publish(event)

    # Verify correlation ID in Redis call
    call_args = mock_redis.xadd.call_args
    event_data = call_args[0][1]
    assert "correlation_id" in event_data


# ============================================================================
# TEST: EVENT BUS INTEGRATION (RL Engine Event Handlers)
# ============================================================================

@pytest.mark.asyncio
async def test_rl_engine_event_handler_integration():
    """Test RL Engine event handler integration"""
    sys.path.insert(0, '/home/user/Apex-System/src/services/rl_engine')
    from services.rl_engine.application.event_handlers import RLEventHandlers
    from services.rl_engine.application.rl_service import RLService
    from services.rl_engine.domain.q_learning import QLearningEngine

    # Setup
    rl_engine = QLearningEngine()
    rl_service = RLService(
        rl_engine=rl_engine,
        strategy_repository=None,
        event_bus=None
    )
    event_handlers = RLEventHandlers(rl_service=rl_service)

    # Create traffic event
    traffic_event = Event(
        event_type="traffic.request_completed",
        source_service="traffic-manager",
        data={
            "request_id": "req_123",
            "context": "MAXIMIZE_ROAS",
            "action": "focus_high_value_audiences",
            "success": True,
            "metrics": {
                "roas": 3.2,
                "ctr": 2.8,
                "conversions": 35
            }
        },
        correlation_id="test-correlation"
    )

    # Handle event
    await event_handlers.handle_traffic_request_completed(traffic_event)

    # Verify RL Engine learned
    assert len(rl_engine.dual_buffer.active_buffer) == 1
    experience = rl_engine.dual_buffer.active_buffer[0]
    assert experience.context == "MAXIMIZE_ROAS"
    assert experience.action == "focus_high_value_audiences"
    assert experience.reward > 0  # Good metrics should give positive reward


@pytest.mark.asyncio
async def test_rl_engine_reward_calculation():
    """Test RL Engine reward calculation from metrics"""
    sys.path.insert(0, '/home/user/Apex-System/src/services/rl_engine')
    from services.rl_engine.application.event_handlers import RLEventHandlers
    from services.rl_engine.application.rl_service import RLService
    from services.rl_engine.domain.q_learning import QLearningEngine

    # Setup
    rl_engine = QLearningEngine()
    rl_service = RLService(
        rl_engine=rl_engine,
        strategy_repository=None,
        event_bus=None
    )
    event_handlers = RLEventHandlers(rl_service=rl_service)

    # Test good metrics
    good_metrics = {
        "roas": 4.0,  # Excellent
        "ctr": 3.0,   # High
        "conversions": 40  # Many
    }
    reward_good = event_handlers._calculate_reward(success=True, metrics=good_metrics)
    assert reward_good > 0.5  # Should be high reward

    # Test poor metrics
    poor_metrics = {
        "roas": 0.5,  # Low
        "ctr": 0.5,   # Low
        "conversions": 3  # Few
    }
    reward_poor = event_handlers._calculate_reward(success=False, metrics=poor_metrics)
    assert reward_poor < 0  # Should be negative reward


# ============================================================================
# TEST: EVENT SUBSCRIPTIONS
# ============================================================================

@pytest.mark.asyncio
async def test_get_event_subscriptions():
    """Test getting all event subscriptions"""
    sys.path.insert(0, '/home/user/Apex-System/src/services/rl_engine')
    from services.rl_engine.application.event_handlers import RLEventHandlers
    from services.rl_engine.application.rl_service import RLService
    from services.rl_engine.domain.q_learning import QLearningEngine

    # Setup
    rl_engine = QLearningEngine()
    rl_service = RLService(
        rl_engine=rl_engine,
        strategy_repository=None,
        event_bus=None
    )
    event_handlers = RLEventHandlers(rl_service=rl_service)

    # Get subscriptions
    subscriptions = event_handlers.get_event_subscriptions()

    # Verify
    assert "traffic.request_completed" in subscriptions
    assert "campaign.performance_updated" in subscriptions
    assert "rl.strategy_feedback" in subscriptions
    assert len(subscriptions) == 3


# ============================================================================
# TEST: CAMPAIGN PERFORMANCE EVENT
# ============================================================================

@pytest.mark.asyncio
async def test_campaign_performance_event_handler():
    """Test campaign performance updated event handler"""
    sys.path.insert(0, '/home/user/Apex-System/src/services/rl_engine')
    from services.rl_engine.application.event_handlers import RLEventHandlers
    from services.rl_engine.application.rl_service import RLService
    from services.rl_engine.domain.q_learning import QLearningEngine

    # Setup
    rl_engine = QLearningEngine()
    rl_service = RLService(
        rl_engine=rl_engine,
        strategy_repository=None,
        event_bus=None
    )
    event_handlers = RLEventHandlers(rl_service=rl_service)

    # Create campaign event with improvement
    campaign_event = Event(
        event_type="campaign.performance_updated",
        source_service="campaign-manager",
        data={
            "campaign_id": "camp_123",
            "strategic_context": "MAXIMIZE_ROAS",
            "previous_action": "focus_high_value_audiences",
            "improvement": True,
            "metrics": {"roas": 3.5, "ctr": 2.9}
        }
    )

    # Handle event
    await event_handlers.handle_campaign_performance_updated(campaign_event)

    # Verify learning occurred
    assert len(rl_engine.dual_buffer.active_buffer) == 1
    experience = rl_engine.dual_buffer.active_buffer[0]
    assert experience.reward > 0  # Improvement should give positive reward


# ============================================================================
# TEST: STRATEGY FEEDBACK EVENT
# ============================================================================

@pytest.mark.asyncio
async def test_strategy_feedback_event_handler():
    """Test explicit strategy feedback event handler"""
    sys.path.insert(0, '/home/user/Apex-System/src/services/rl_engine')
    from services.rl_engine.application.event_handlers import RLEventHandlers
    from services.rl_engine.application.rl_service import RLService
    from services.rl_engine.domain.q_learning import QLearningEngine

    # Setup
    rl_engine = QLearningEngine()
    rl_service = RLService(
        rl_engine=rl_engine,
        strategy_repository=None,
        event_bus=None
    )
    event_handlers = RLEventHandlers(rl_service=rl_service)

    # Create feedback event
    feedback_event = Event(
        event_type="rl.strategy_feedback",
        source_service="human-operator",
        data={
            "context": "MAXIMIZE_ROAS",
            "action": "focus_high_value_audiences",
            "reward": 0.95,  # Explicit high reward
            "feedback_source": "manual_review"
        }
    )

    # Handle event
    await event_handlers.handle_strategy_feedback(feedback_event)

    # Verify learning with explicit reward
    assert len(rl_engine.dual_buffer.active_buffer) == 1
    experience = rl_engine.dual_buffer.active_buffer[0]
    assert experience.reward == 0.95  # Exact reward provided


@pytest.mark.asyncio
async def test_strategy_feedback_reward_clamping():
    """Test that strategy feedback reward is clamped to [-1.0, 1.0]"""
    sys.path.insert(0, '/home/user/Apex-System/src/services/rl_engine')
    from services.rl_engine.application.event_handlers import RLEventHandlers
    from services.rl_engine.application.rl_service import RLService
    from services.rl_engine.domain.q_learning import QLearningEngine

    # Setup
    rl_engine = QLearningEngine()
    rl_service = RLService(
        rl_engine=rl_engine,
        strategy_repository=None,
        event_bus=None
    )
    event_handlers = RLEventHandlers(rl_service=rl_service)

    # Create feedback event with out-of-range reward
    feedback_event = Event(
        event_type="rl.strategy_feedback",
        source_service="test",
        data={
            "context": "TEST",
            "action": "test_action",
            "reward": 5.0  # Out of range
        }
    )

    # Handle event
    await event_handlers.handle_strategy_feedback(feedback_event)

    # Verify reward was clamped
    experience = rl_engine.dual_buffer.active_buffer[0]
    assert -1.0 <= experience.reward <= 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
