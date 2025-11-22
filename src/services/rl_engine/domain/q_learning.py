"""
RL Engine - Domain Layer - Q-Learning Algorithm
Pure Q-Learning implementation without framework dependencies
"""

from typing import Dict, List, Tuple, Optional
import random
import statistics
from datetime import datetime

from .models import (
    QTable,
    Strategy,
    Experience,
    DualBuffer,
    ActionType,
    CampaignContext,
    CampaignMetrics,
    RiskAppetite,
    InvalidRewardException,
    InvalidContextException,
    InvalidActionException
)


class QLearningEngine:
    """
    Pure Q-Learning Engine implementing Reinforcement Learning algorithm

    This class contains ONLY business logic - no infrastructure dependencies
    All I/O operations are abstracted to repositories
    """

    def __init__(
        self,
        learning_rate: float = 0.1,
        discount_factor: float = 0.95,
        exploration_rate: float = 0.15,
        max_active_buffer: int = 25,
        max_history_buffer: int = 1000,
        auto_process_threshold: int = 15,
        history_retention_hours: int = 72
    ):
        """Initialize Q-Learning Engine with hyperparameters"""
        # Hyperparameters
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.exploration_rate = exploration_rate

        # Core data structures
        self.q_table = QTable(
            learning_rate=learning_rate,
            discount_factor=discount_factor
        )
        self.strategies: Dict[str, Strategy] = {}
        self.dual_buffer = DualBuffer(
            max_active_size=max_active_buffer,
            max_history_size=max_history_buffer,
            auto_process_threshold=auto_process_threshold,
            history_retention_hours=history_retention_hours
        )

        # Available actions
        self.available_actions = [action.value for action in ActionType]

        # Metrics
        self.total_actions = 0
        self.total_learning_sessions = 0
        self.total_experiences_processed = 0
        self.confidence_history: List[float] = []
        self.reward_history: List[float] = []
        self.q_value_history: List[float] = []

    def add_experience(
        self,
        context: str,
        action: str,
        reward: float,
        metadata: Optional[Dict] = None
    ) -> Experience:
        """
        Business Rule: Add a new experience to the learning buffer

        Args:
            context: Strategic context (e.g., "MAXIMIZE_ROAS")
            action: Action taken
            reward: Reward received (-1.0 to 1.0)
            metadata: Additional metadata

        Returns:
            Created Experience entity
        """
        # Validate inputs
        if not context or not context.strip():
            raise InvalidContextException("Context cannot be empty")

        if action not in self.available_actions:
            raise InvalidActionException(f"Invalid action: {action}")

        if not -1.0 <= reward <= 1.0:
            raise InvalidRewardException(f"Reward must be between -1.0 and 1.0, got {reward}")

        # Create experience
        import uuid
        experience = Experience(
            id=str(uuid.uuid4()),
            context=context,
            action=action,
            reward=reward,
            timestamp=datetime.utcnow(),
            metadata=metadata or {}
        )

        # Add to dual buffer
        self.dual_buffer.add_experience(experience)

        # Track reward
        self.reward_history.append(reward)
        if len(self.reward_history) > 1000:
            self.reward_history = self.reward_history[-500:]

        return experience

    def should_process_experiences(self) -> bool:
        """Business Rule: Should we process experiences now?"""
        return self.dual_buffer.should_auto_process()

    def process_experiences(self) -> Dict:
        """
        Business Rule: Process all unprocessed experiences using Q-Learning

        This implements the core Q-Learning update:
        Q(s,a) = Q(s,a) + α * [R + γ * max(Q(s',a')) - Q(s,a)]

        Returns:
            Processing statistics
        """
        unprocessed = self.dual_buffer.get_unprocessed_experiences()

        if not unprocessed:
            return {
                "processed_count": 0,
                "strategies_created": 0,
                "strategies_updated": 0,
                "avg_q_value": 0.0
            }

        processed_count = 0
        strategies_created = 0
        strategies_updated = 0
        new_q_values = []

        for experience in unprocessed:
            # Apply Q-Learning update
            new_q = self.q_table.update_q_value(
                context=experience.context,
                action=experience.action,
                reward=experience.reward
            )
            new_q_values.append(new_q)

            # Update or create strategy
            if experience.context not in self.strategies:
                # Create new strategy
                strategy = Strategy(
                    context=experience.context,
                    best_action=experience.action,
                    best_q_value=new_q,
                    algorithm_version="q_learning_v1"
                )
                self.strategies[experience.context] = strategy
                strategies_created += 1
            else:
                # Update existing strategy
                strategy = self.strategies[experience.context]
                strategies_updated += 1

            # Update strategy with action result
            strategy.update_with_action(
                action=experience.action,
                q_value=new_q,
                reward=experience.reward
            )

            # Mark as processed
            experience.mark_processed()
            processed_count += 1

        # Move to history
        self.dual_buffer.move_to_history(unprocessed)

        # Update metrics
        self.total_experiences_processed += processed_count
        self.total_learning_sessions += 1

        if new_q_values:
            self.q_value_history.extend(new_q_values)
            if len(self.q_value_history) > 1000:
                self.q_value_history = self.q_value_history[-500:]

        return {
            "processed_count": processed_count,
            "strategies_created": strategies_created,
            "strategies_updated": strategies_updated,
            "avg_q_value": statistics.mean(new_q_values) if new_q_values else 0.0,
            "total_strategies": len(self.strategies)
        }

    def generate_action(
        self,
        context: CampaignContext,
        metrics: CampaignMetrics
    ) -> Tuple[str, float, str]:
        """
        Business Rule: Generate best action for current context

        Uses Epsilon-Greedy strategy:
        - With probability ε: explore (random action)
        - With probability 1-ε: exploit (best known action)

        Args:
            context: Campaign context
            metrics: Campaign metrics

        Returns:
            Tuple of (action, confidence, reasoning)
        """
        self.total_actions += 1

        # Normalize context
        normalized_context = context.normalize()

        # Check if we have a learned strategy
        if normalized_context in self.strategies:
            strategy = self.strategies[normalized_context]

            # Epsilon-greedy: explore vs exploit
            if strategy.should_explore(self.exploration_rate):
                # Explore: random action
                action = self.q_table.get_random_action(self.available_actions)
                confidence = 0.5  # Medium confidence for exploration
                reasoning = f"Exploration: random action from {len(self.available_actions)} available"
            else:
                # Exploit: best known action
                action = strategy.best_action
                confidence = strategy.get_confidence()
                reasoning = f"Exploitation: best action from {strategy.total_experiences} experiences"

        elif normalized_context in self.q_table.table:
            # We have Q-values but no strategy yet
            action = self.q_table.get_best_action(normalized_context, self.available_actions)
            if action:
                q_value = self.q_table.get_q_value(normalized_context, action)
                confidence = min(0.9, 0.4 + (q_value * 0.1))
                reasoning = f"Q-table match: Q-value={q_value:.3f}"
            else:
                # Fallback to heuristic
                action, confidence, reasoning = self._get_heuristic_action(context, metrics)
        else:
            # No learned data - use heuristic
            action, confidence, reasoning = self._get_heuristic_action(context, metrics)

        # Track confidence
        self.confidence_history.append(confidence)
        if len(self.confidence_history) > 1000:
            self.confidence_history = self.confidence_history[-500:]

        return action, confidence, reasoning

    def _get_heuristic_action(
        self,
        context: CampaignContext,
        metrics: CampaignMetrics
    ) -> Tuple[str, float, str]:
        """
        Business Rule: Heuristic fallback for unknown contexts
        Uses domain knowledge to suggest reasonable actions
        """
        context_lower = context.strategic_context.lower()

        # CPA optimization
        if "minimize_cpa" in context_lower or "cpa" in context_lower:
            if metrics.roas < 2.0:
                return (
                    ActionType.FOCUS_HIGH_VALUE_AUDIENCES.value,
                    0.5,
                    "Heuristic: Low ROAS - focus on high-value audiences"
                )
            return (
                ActionType.REDUCE_BID_CONSERVATIVE.value,
                0.5,
                "Heuristic: CPA optimization"
            )

        # ROAS optimization
        if "maximize_roas" in context_lower or "roas" in context_lower:
            return (
                ActionType.FOCUS_HIGH_VALUE_AUDIENCES.value,
                0.5,
                "Heuristic: ROAS maximization"
            )

        # Brand awareness
        if "brand_awareness" in context_lower or "awareness" in context_lower:
            return (
                ActionType.EXPAND_REACH_CAMPAIGNS.value,
                0.5,
                "Heuristic: Brand awareness campaign"
            )

        # Conversions
        if "conversions" in context_lower or "conversion" in context_lower:
            return (
                ActionType.INCREASE_BID_CONVERSION_KEYWORDS.value,
                0.5,
                "Heuristic: Conversion optimization"
            )

        # Reach
        if "reach" in context_lower:
            return (
                ActionType.EXPAND_REACH_CAMPAIGNS.value,
                0.5,
                "Heuristic: Reach maximization"
            )

        # CTR
        if "ctr" in context_lower:
            return (
                ActionType.OPTIMIZE_FOR_CTR.value,
                0.5,
                "Heuristic: CTR optimization"
            )

        # Default fallback
        return (
            ActionType.OPTIMIZE_BIDDING_STRATEGY.value,
            0.5,
            "Heuristic: Default optimization"
        )

    def get_learning_metrics(self) -> Dict:
        """Get current learning metrics"""
        avg_confidence = statistics.mean(self.confidence_history) if self.confidence_history else 0.0
        avg_reward = statistics.mean(self.reward_history) if self.reward_history else 0.0
        avg_q_value = statistics.mean(self.q_value_history) if self.q_value_history else 0.0

        return {
            "total_actions": self.total_actions,
            "total_learning_sessions": self.total_learning_sessions,
            "total_experiences_processed": self.total_experiences_processed,
            "total_strategies": len(self.strategies),
            "avg_confidence": round(avg_confidence, 3),
            "avg_reward": round(avg_reward, 3),
            "avg_q_value": round(avg_q_value, 3),
            "max_q_value": round(max(self.q_value_history), 3) if self.q_value_history else 0.0,
            "dual_buffer_metrics": {
                "active_buffer_size": len(self.dual_buffer.active_buffer),
                "active_buffer_max": self.dual_buffer.max_active_size,
                "active_buffer_utilization_percent": round(
                    self.dual_buffer.get_active_buffer_utilization(), 2
                ),
                "history_buffer_size": len(self.dual_buffer.history_buffer),
                "history_buffer_max": self.dual_buffer.max_history_size,
                "history_buffer_utilization_percent": round(
                    self.dual_buffer.get_history_buffer_utilization(), 2
                ),
            },
            "hyperparameters": {
                "learning_rate": self.learning_rate,
                "discount_factor": self.discount_factor,
                "exploration_rate": self.exploration_rate
            }
        }

    def get_strategy(self, context: str) -> Optional[Strategy]:
        """Get learned strategy for a context"""
        return self.strategies.get(context)

    def get_all_strategies(self) -> Dict[str, Strategy]:
        """Get all learned strategies"""
        return self.strategies

    def load_strategies(self, strategies: Dict[str, Dict]) -> None:
        """Load strategies from persistence"""
        for context, strategy_data in strategies.items():
            self.strategies[context] = Strategy(
                context=context,
                best_action=strategy_data.get("best_action", ""),
                best_q_value=strategy_data.get("best_q_value", 0.0),
                total_experiences=strategy_data.get("total_experiences", 0),
                actions_count=strategy_data.get("actions_count", 0),
                action_details=strategy_data.get("action_details", {}),
                q_values=strategy_data.get("q_values", {}),
                algorithm_version=strategy_data.get("algorithm_version", "q_learning_v1")
            )

    def load_q_table(self, q_table_data: Dict[str, Dict[str, float]]) -> None:
        """Load Q-table from persistence"""
        self.q_table.table = q_table_data
