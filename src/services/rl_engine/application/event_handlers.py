"""
RL Engine - Application Layer - Event Handlers
Handles events from Event Bus for event-driven learning
"""

import logging
from typing import Dict, Any

from common.event_bus import Event
from .rl_service import RLService


logger = logging.getLogger(__name__)


class RLEventHandlers:
    """
    Event Handlers for RL Engine

    Subscribes to events from other services to learn automatically
    Key event: traffic.request_completed - learn from completed requests
    """

    def __init__(self, rl_service: RLService):
        """
        Initialize event handlers

        Args:
            rl_service: RL Service instance
        """
        self.rl_service = rl_service

    async def handle_traffic_request_completed(self, event: Event) -> None:
        """
        Event Handler: traffic.request_completed

        When Traffic Manager completes a request, extract metrics and learn

        Event data expected:
        {
            "request_id": str,
            "context": str,  # Strategic context
            "action": str,  # Action taken
            "metrics": {
                "ctr": float,
                "roas": float,
                "conversions": int,
                ...
            },
            "success": bool,
            "response_time_ms": float
        }
        """
        try:
            data = event.data

            # Extract relevant fields
            context = data.get("context", "UNKNOWN")
            action = data.get("action", "optimize_bidding_strategy")
            success = data.get("success", False)
            metrics = data.get("metrics", {})

            # Calculate reward based on success and metrics
            reward = self._calculate_reward(success, metrics)

            # Learn from experience
            await self.rl_service.learn_from_experience(
                context=context,
                action=action,
                reward=reward,
                metadata={
                    "request_id": data.get("request_id"),
                    "event_id": event.event_id,
                    "event_timestamp": event.timestamp,
                    "metrics": metrics,
                    "response_time_ms": data.get("response_time_ms", 0)
                },
                correlation_id=event.correlation_id
            )

            logger.info(
                f"Learned from traffic event: {context} → {action} "
                f"(reward: {reward:.3f}, correlation_id: {event.correlation_id})"
            )

        except Exception as e:
            logger.error(f"Error handling traffic request completed event: {e}", exc_info=True)

    async def handle_campaign_performance_updated(self, event: Event) -> None:
        """
        Event Handler: campaign.performance_updated

        When campaign performance is updated, learn from the results

        Event data expected:
        {
            "campaign_id": str,
            "strategic_context": str,
            "previous_action": str,
            "metrics": {...},
            "improvement": bool
        }
        """
        try:
            data = event.data

            context = data.get("strategic_context", "UNKNOWN")
            action = data.get("previous_action", "optimize_bidding_strategy")
            improvement = data.get("improvement", False)
            metrics = data.get("metrics", {})

            # Reward based on improvement
            reward = 0.5 if improvement else -0.3

            # Adjust reward based on metrics
            if metrics.get("roas", 0) > 3.0:
                reward += 0.3
            elif metrics.get("roas", 0) < 1.0:
                reward -= 0.3

            # Learn from experience
            await self.rl_service.learn_from_experience(
                context=context,
                action=action,
                reward=reward,
                metadata={
                    "campaign_id": data.get("campaign_id"),
                    "event_id": event.event_id,
                    "metrics": metrics,
                    "improvement": improvement
                },
                correlation_id=event.correlation_id
            )

            logger.info(
                f"Learned from campaign performance: {context} → {action} "
                f"(reward: {reward:.3f}, improvement: {improvement})"
            )

        except Exception as e:
            logger.error(f"Error handling campaign performance event: {e}", exc_info=True)

    async def handle_strategy_feedback(self, event: Event) -> None:
        """
        Event Handler: rl.strategy_feedback

        Explicit feedback on strategy performance from other services

        Event data expected:
        {
            "context": str,
            "action": str,
            "reward": float,
            "feedback_source": str,
            "metadata": {...}
        }
        """
        try:
            data = event.data

            context = data.get("context", "UNKNOWN")
            action = data.get("action", "optimize_bidding_strategy")
            reward = float(data.get("reward", 0.0))

            # Validate reward range
            reward = max(-1.0, min(1.0, reward))

            # Learn from experience
            await self.rl_service.learn_from_experience(
                context=context,
                action=action,
                reward=reward,
                metadata={
                    "event_id": event.event_id,
                    "feedback_source": data.get("feedback_source", "unknown"),
                    "metadata": data.get("metadata", {})
                },
                correlation_id=event.correlation_id
            )

            logger.info(
                f"Learned from explicit feedback: {context} → {action} "
                f"(reward: {reward:.3f}, source: {data.get('feedback_source')})"
            )

        except Exception as e:
            logger.error(f"Error handling strategy feedback event: {e}", exc_info=True)

    def _calculate_reward(self, success: bool, metrics: Dict[str, Any]) -> float:
        """
        Business Rule: Calculate reward from request success and metrics

        Reward calculation:
        - Base reward: +0.5 for success, -0.5 for failure
        - ROAS bonus: +0.3 if > 3.0, -0.3 if < 1.0
        - CTR bonus: +0.2 if > 2.5, -0.2 if < 0.8
        - Conversions bonus: +0.1 if > 30, no penalty

        Final reward is clamped to [-1.0, 1.0]
        """
        # Base reward
        reward = 0.5 if success else -0.5

        # ROAS adjustment
        roas = metrics.get("roas", 0.0)
        if roas > 3.0:
            reward += 0.3
        elif roas < 1.0:
            reward -= 0.3

        # CTR adjustment
        ctr = metrics.get("ctr", 0.0)
        if ctr > 2.5:
            reward += 0.2
        elif ctr < 0.8:
            reward -= 0.2

        # Conversions bonus (only positive)
        conversions = metrics.get("conversions", 0)
        if conversions > 30:
            reward += 0.1

        # Clamp to [-1.0, 1.0]
        reward = max(-1.0, min(1.0, reward))

        return reward

    def get_event_subscriptions(self) -> Dict[str, callable]:
        """
        Get all event subscriptions

        Returns:
            Dict mapping event_type to handler function
        """
        return {
            "traffic.request_completed": self.handle_traffic_request_completed,
            "campaign.performance_updated": self.handle_campaign_performance_updated,
            "rl.strategy_feedback": self.handle_strategy_feedback
        }
