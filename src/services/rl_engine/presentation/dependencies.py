"""
RL Engine - Presentation Layer - Dependency Injection
FastAPI dependencies for RL Engine services
"""

from functools import lru_cache
import logging

from domain.q_learning import QLearningEngine
from application.rl_service import RLService
from application.event_handlers import RLEventHandlers
from infrastructure.repositories import MongoRLRepository
from infrastructure.config import get_settings
from infrastructure.database import get_database
from common.event_bus import get_event_bus


logger = logging.getLogger(__name__)


# Singleton instances
_rl_engine: QLearningEngine = None
_rl_service: RLService = None
_rl_event_handlers: RLEventHandlers = None
_rl_repository: MongoRLRepository = None


async def get_rl_repository() -> MongoRLRepository:
    """Get MongoDB repository singleton"""
    global _rl_repository

    if _rl_repository is None:
        db = await get_database()
        _rl_repository = MongoRLRepository(db)
        logger.info("MongoDB RL Repository initialized")

    return _rl_repository


async def get_rl_engine() -> QLearningEngine:
    """Get Q-Learning engine singleton"""
    global _rl_engine

    if _rl_engine is None:
        settings = get_settings()

        _rl_engine = QLearningEngine(
            learning_rate=settings.learning_rate,
            discount_factor=settings.discount_factor,
            exploration_rate=settings.exploration_rate,
            max_active_buffer=settings.max_active_buffer,
            max_history_buffer=settings.max_history_buffer,
            auto_process_threshold=settings.auto_process_threshold,
            history_retention_hours=settings.history_retention_hours
        )

        # Load persisted data
        repository = await get_rl_repository()
        strategies = await repository.load_strategies()
        q_table = await repository.load_q_table()

        if strategies:
            _rl_engine.load_strategies(strategies)
            logger.info(f"Loaded {len(strategies)} strategies from MongoDB")

        if q_table:
            _rl_engine.load_q_table(q_table)
            logger.info(f"Loaded Q-table with {len(q_table)} contexts from MongoDB")

        logger.info("Q-Learning Engine initialized")

    return _rl_engine


async def get_rl_service() -> RLService:
    """Get RL service singleton"""
    global _rl_service

    if _rl_service is None:
        rl_engine = await get_rl_engine()
        repository = await get_rl_repository()

        # Get event bus if enabled
        settings = get_settings()
        event_bus = None
        if settings.event_bus_enabled:
            try:
                event_bus = await get_event_bus()
                logger.info("Event Bus connected for RL Service")
            except Exception as e:
                logger.warning(f"Failed to connect Event Bus: {e}")

        _rl_service = RLService(
            rl_engine=rl_engine,
            strategy_repository=repository,
            event_bus=event_bus
        )

        logger.info("RL Service initialized")

    return _rl_service


async def get_event_handlers() -> RLEventHandlers:
    """Get event handlers singleton"""
    global _rl_event_handlers

    if _rl_event_handlers is None:
        rl_service = await get_rl_service()
        _rl_event_handlers = RLEventHandlers(rl_service=rl_service)
        logger.info("RL Event Handlers initialized")

    return _rl_event_handlers


async def initialize_event_subscriptions():
    """Initialize event subscriptions for event-driven learning"""
    try:
        settings = get_settings()

        if not settings.event_bus_enabled:
            logger.info("Event Bus disabled - skipping event subscriptions")
            return

        event_bus = await get_event_bus()
        event_handlers = await get_event_handlers()

        # Get all subscriptions
        subscriptions = event_handlers.get_event_subscriptions()

        # Subscribe to each event type
        for event_type, handler in subscriptions.items():
            await event_bus.subscribe(event_type, handler)
            logger.info(f"Subscribed to event: {event_type}")

        logger.info(f"✅ Event subscriptions initialized: {len(subscriptions)} event types")

    except Exception as e:
        logger.error(f"Failed to initialize event subscriptions: {e}", exc_info=True)


async def cleanup_resources():
    """Cleanup resources on shutdown"""
    global _rl_engine, _rl_service, _rl_event_handlers, _rl_repository

    try:
        # Save current state before shutdown
        if _rl_service and _rl_repository:
            strategies = _rl_engine.get_all_strategies()

            # Convert to serializable format
            strategies_dict = {}
            for context, strategy in strategies.items():
                strategies_dict[context] = {
                    "context": strategy.context,
                    "best_action": strategy.best_action,
                    "best_q_value": strategy.best_q_value,
                    "total_experiences": strategy.total_experiences,
                    "actions_count": strategy.actions_count,
                    "action_details": strategy.action_details,
                    "q_values": strategy.q_values,
                    "created_at": strategy.created_at.isoformat(),
                    "last_updated": strategy.last_updated.isoformat(),
                    "algorithm_version": strategy.algorithm_version
                }

            await _rl_repository.save_strategies(strategies_dict)

            # Save Q-table
            for context, q_values in _rl_engine.q_table.table.items():
                await _rl_repository.save_q_table(context, q_values)

            logger.info("Saved RL Engine state before shutdown")

    except Exception as e:
        logger.error(f"Error during cleanup: {e}", exc_info=True)

    # Reset singletons
    _rl_engine = None
    _rl_service = None
    _rl_event_handlers = None
    _rl_repository = None
