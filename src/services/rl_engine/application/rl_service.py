"""
RL Engine - Application Layer - RL Service
Orchestrates Q-Learning engine and handles business workflows
"""

from typing import Dict, Any, Optional, Tuple
from datetime import datetime
import logging

from domain.q_learning import QLearningEngine
from domain.models import (
    CampaignContext,
    CampaignMetrics,
    CampaignType,
    RiskAppetite,
    Competition,
    Experience,
    Strategy
)


logger = logging.getLogger(__name__)


class RLService:
    """
    RL Service - Application Layer

    Orchestrates Q-Learning operations and coordinates with infrastructure
    Implements use cases like: generate action, learn from experience, process batch
    """

    def __init__(
        self,
        rl_engine: QLearningEngine,
        strategy_repository=None,
        event_bus=None
    ):
        """
        Initialize RL Service

        Args:
            rl_engine: Q-Learning engine (domain)
            strategy_repository: Repository for persisting strategies
            event_bus: Event bus for publishing events
        """
        self.rl_engine = rl_engine
        self.strategy_repository = strategy_repository
        self.event_bus = event_bus

    async def generate_action(
        self,
        strategic_context: str,
        campaign_type: str = "conversion",
        risk_appetite: str = "moderate",
        competition: str = "moderate",
        ctr: float = 2.0,
        cpm: float = 10.0,
        cpc: float = 0.5,
        impressions: int = 10000,
        clicks: int = 200,
        conversions: int = 20,
        spend: float = 100.0,
        revenue: float = 200.0,
        roas: float = 2.0,
        budget_utilization: float = 0.8,
        reach: int = 8000,
        frequency: float = 1.25,
        **context_kwargs
    ) -> Dict[str, Any]:
        """
        Use Case: Generate optimal action for current campaign state

        Args:
            strategic_context: Main strategic goal
            campaign_type: Type of campaign
            risk_appetite: Risk level
            competition: Competition level
            ctr, cpm, cpc, etc.: Campaign metrics
            **context_kwargs: Additional context parameters

        Returns:
            Action recommendation with confidence and reasoning
        """
        try:
            # Build domain objects
            context = CampaignContext(
                strategic_context=strategic_context,
                campaign_type=CampaignType(campaign_type),
                risk_appetite=RiskAppetite(risk_appetite),
                competition=Competition(competition),
                time_of_day=context_kwargs.get("time_of_day", "business_hours"),
                day_of_week=context_kwargs.get("day_of_week", "weekday"),
                seasonality=context_kwargs.get("seasonality", "normal"),
                market_conditions=context_kwargs.get("market_conditions", "stable"),
                brazil_region=context_kwargs.get("brazil_region", "southeast")
            )

            metrics = CampaignMetrics(
                ctr=ctr,
                cpm=cpm,
                cpc=cpc,
                impressions=impressions,
                clicks=clicks,
                conversions=conversions,
                spend=spend,
                revenue=revenue,
                roas=roas,
                budget_utilization=budget_utilization,
                reach=reach,
                frequency=frequency
            )

            # Generate action using Q-Learning engine
            action, confidence, reasoning = self.rl_engine.generate_action(context, metrics)

            result = {
                "action": action,
                "confidence": confidence,
                "reasoning": reasoning,
                "context": {
                    "strategic_context": strategic_context,
                    "normalized_context": context.normalize(),
                    "campaign_type": campaign_type,
                    "risk_appetite": risk_appetite,
                    "competition": competition
                },
                "metrics": {
                    "ctr": ctr,
                    "roas": roas,
                    "conversions": conversions,
                    "budget_utilization": budget_utilization
                },
                "timestamp": datetime.utcnow().isoformat(),
                "dual_buffer_status": {
                    "active_buffer_size": len(self.rl_engine.dual_buffer.active_buffer),
                    "history_size": len(self.rl_engine.dual_buffer.history_buffer),
                    "total_strategies": len(self.rl_engine.strategies)
                }
            }

            logger.info(
                f"Action generated: {action} (confidence: {confidence:.3f}, "
                f"context: {context.normalize()})"
            )

            return result

        except Exception as e:
            logger.error(f"Error generating action: {e}", exc_info=True)
            # Return safe fallback
            return {
                "action": "optimize_bidding_strategy",
                "confidence": 0.1,
                "reasoning": f"Fallback due to error: {str(e)}",
                "context": {"strategic_context": strategic_context},
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }

    async def learn_from_experience(
        self,
        context: str,
        action: str,
        reward: float,
        metadata: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Use Case: Learn from a single experience

        Args:
            context: Strategic context
            action: Action taken
            reward: Reward received (-1.0 to 1.0)
            metadata: Additional metadata
            correlation_id: For tracing

        Returns:
            Learning result
        """
        try:
            # Add experience to buffer
            experience = self.rl_engine.add_experience(
                context=context,
                action=action,
                reward=reward,
                metadata=metadata or {}
            )

            # Check if we should auto-process
            should_process = self.rl_engine.should_process_experiences()

            result = {
                "status": "learned",
                "experience_id": experience.id,
                "buffer_size": len(self.rl_engine.dual_buffer.active_buffer),
                "history_size": len(self.rl_engine.dual_buffer.history_buffer),
                "strategies_count": len(self.rl_engine.strategies),
                "timestamp": experience.timestamp.isoformat(),
                "auto_processing_triggered": should_process
            }

            # Auto-process if threshold reached
            if should_process:
                logger.info(
                    f"Auto-processing triggered: "
                    f"{len(self.rl_engine.dual_buffer.active_buffer)} experiences in buffer"
                )
                processing_result = await self.process_experiences()
                result["processing_result"] = processing_result

            # Publish event if event bus available
            if self.event_bus:
                await self._publish_experience_learned_event(
                    experience, correlation_id
                )

            logger.info(
                f"Experience learned: {context} → {action} (reward: {reward}, "
                f"buffer: {result['buffer_size']})"
            )

            return result

        except Exception as e:
            logger.error(f"Error learning from experience: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    async def process_experiences(self) -> Dict[str, Any]:
        """
        Use Case: Force process all unprocessed experiences

        Returns:
            Processing statistics
        """
        try:
            initial_buffer_size = len(self.rl_engine.dual_buffer.active_buffer)
            initial_history_size = len(self.rl_engine.dual_buffer.history_buffer)

            if initial_buffer_size == 0:
                return {
                    "status": "no_experiences_to_process",
                    "message": "Buffer is empty",
                    "buffer_size": 0
                }

            # Process using Q-Learning
            stats = self.rl_engine.process_experiences()

            final_buffer_size = len(self.rl_engine.dual_buffer.active_buffer)
            final_history_size = len(self.rl_engine.dual_buffer.history_buffer)

            # Persist strategies if repository available
            if self.strategy_repository:
                await self._save_strategies()

            # Publish event if event bus available
            if self.event_bus:
                await self._publish_batch_processed_event(stats)

            result = {
                "status": "processing_completed",
                "experiences_processed": stats["processed_count"],
                "strategies_created": stats["strategies_created"],
                "strategies_updated": stats["strategies_updated"],
                "avg_q_value": stats["avg_q_value"],
                "moved_to_history": final_history_size - initial_history_size,
                "final_buffer_size": final_buffer_size,
                "final_history_size": final_history_size,
                "total_strategies": stats["total_strategies"],
                "timestamp": datetime.utcnow().isoformat()
            }

            logger.info(
                f"Batch processing completed: {stats['processed_count']} experiences, "
                f"{stats['strategies_created']} new strategies, "
                f"{stats['strategies_updated']} updated"
            )

            return result

        except Exception as e:
            logger.error(f"Error processing experiences: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    async def get_strategies(self) -> Dict[str, Any]:
        """
        Use Case: Get all learned strategies

        Returns:
            All strategies with metadata
        """
        try:
            strategies = self.rl_engine.get_all_strategies()

            # Convert to serializable format
            strategies_dict = {}
            for context, strategy in strategies.items():
                strategies_dict[context] = {
                    "context": strategy.context,
                    "best_action": strategy.best_action,
                    "best_q_value": strategy.best_q_value,
                    "total_experiences": strategy.total_experiences,
                    "actions_count": strategy.actions_count,
                    "confidence": strategy.get_confidence(),
                    "action_details": strategy.action_details,
                    "q_values": strategy.q_values,
                    "created_at": strategy.created_at.isoformat(),
                    "last_updated": strategy.last_updated.isoformat(),
                    "algorithm_version": strategy.algorithm_version
                }

            return {
                "strategies": strategies_dict,
                "count": len(strategies_dict),
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting strategies: {e}", exc_info=True)
            return {
                "strategies": {},
                "count": 0,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    async def get_metrics(self) -> Dict[str, Any]:
        """
        Use Case: Get learning metrics

        Returns:
            Performance metrics
        """
        try:
            return self.rl_engine.get_learning_metrics()
        except Exception as e:
            logger.error(f"Error getting metrics: {e}", exc_info=True)
            return {"error": str(e)}

    async def get_buffer_status(self, buffer_type: str) -> Dict[str, Any]:
        """
        Use Case: Get buffer status

        Args:
            buffer_type: "active" or "history"

        Returns:
            Buffer status
        """
        try:
            dual_buffer = self.rl_engine.dual_buffer

            if buffer_type == "active":
                buffer_data = dual_buffer.active_buffer
                max_size = dual_buffer.max_active_size
                utilization = dual_buffer.get_active_buffer_utilization()
            elif buffer_type == "history":
                buffer_data = dual_buffer.history_buffer
                max_size = dual_buffer.max_history_size
                utilization = dual_buffer.get_history_buffer_utilization()
            else:
                raise ValueError(f"Invalid buffer type: {buffer_type}")

            # Get oldest and newest
            oldest_entry = None
            newest_entry = None
            last_processed = None

            if buffer_data:
                sorted_data = sorted(buffer_data, key=lambda x: x.timestamp)
                oldest_entry = sorted_data[0].timestamp.isoformat()
                newest_entry = sorted_data[-1].timestamp.isoformat()

                # Find last processed
                processed_exps = [exp for exp in buffer_data if exp.processed]
                if processed_exps:
                    last_processed_exp = max(processed_exps, key=lambda x: x.processed_at or datetime.min)
                    if last_processed_exp.processed_at:
                        last_processed = last_processed_exp.processed_at.isoformat()

            # Convert experiences to dict
            experiences_data = [
                {
                    "id": exp.id,
                    "context": exp.context,
                    "action": exp.action,
                    "reward": exp.reward,
                    "timestamp": exp.timestamp.isoformat(),
                    "processed": exp.processed,
                    "processed_at": exp.processed_at.isoformat() if exp.processed_at else None,
                    "age_minutes": exp.age_minutes()
                }
                for exp in buffer_data
            ]

            return {
                "buffer_type": buffer_type,
                "size": len(buffer_data),
                "max_size": max_size,
                "utilization_percent": round(utilization, 2),
                "oldest_entry": oldest_entry,
                "newest_entry": newest_entry,
                "last_processed": last_processed,
                "experiences": experiences_data
            }

        except Exception as e:
            logger.error(f"Error getting buffer status: {e}", exc_info=True)
            return {
                "buffer_type": buffer_type,
                "size": 0,
                "max_size": 0,
                "utilization_percent": 0,
                "error": str(e)
            }

    async def _save_strategies(self) -> None:
        """Save strategies to repository"""
        if not self.strategy_repository:
            return

        try:
            strategies = self.rl_engine.get_all_strategies()

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

            await self.strategy_repository.save_strategies(strategies_dict)
            logger.info(f"Strategies saved: {len(strategies_dict)} strategies")

        except Exception as e:
            logger.error(f"Error saving strategies: {e}", exc_info=True)

    async def _publish_experience_learned_event(
        self,
        experience: Experience,
        correlation_id: Optional[str] = None
    ) -> None:
        """Publish experience learned event"""
        if not self.event_bus:
            return

        try:
            from common.event_bus import Event, EventPriority

            event = Event(
                event_type="rl.experience_learned",
                source_service="rl-engine",
                data={
                    "experience_id": experience.id,
                    "context": experience.context,
                    "action": experience.action,
                    "reward": experience.reward,
                    "timestamp": experience.timestamp.isoformat()
                },
                priority=EventPriority.MEDIUM,
                correlation_id=correlation_id
            )

            await self.event_bus.publish(event)

        except Exception as e:
            logger.warning(f"Failed to publish experience learned event: {e}")

    async def _publish_batch_processed_event(self, stats: Dict) -> None:
        """Publish batch processed event"""
        if not self.event_bus:
            return

        try:
            from common.event_bus import Event, EventPriority

            event = Event(
                event_type="rl.batch_processed",
                source_service="rl-engine",
                data={
                    "processed_count": stats["processed_count"],
                    "strategies_created": stats["strategies_created"],
                    "strategies_updated": stats["strategies_updated"],
                    "avg_q_value": stats["avg_q_value"],
                    "total_strategies": stats["total_strategies"]
                },
                priority=EventPriority.LOW
            )

            await self.event_bus.publish(event)

        except Exception as e:
            logger.warning(f"Failed to publish batch processed event: {e}")
