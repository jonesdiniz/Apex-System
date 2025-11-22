"""
RL Engine - Domain Layer - Pure Business Entities
Contains core domain models for Reinforcement Learning without framework dependencies
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from enum import Enum


# ============================================================================
# ENUMS
# ============================================================================

class ActionType(str, Enum):
    """Available actions for campaign optimization"""
    OPTIMIZE_BIDDING_STRATEGY = "optimize_bidding_strategy"
    INCREASE_BID_CONVERSION_KEYWORDS = "increase_bid_conversion_keywords"
    REDUCE_BID_CONSERVATIVE = "reduce_bid_conservative"
    FOCUS_HIGH_VALUE_AUDIENCES = "focus_high_value_audiences"
    EXPAND_REACH_CAMPAIGNS = "expand_reach_campaigns"
    PAUSE_CAMPAIGN = "pause_campaign"
    INCREASE_BUDGET_MODERATE = "increase_budget_moderate"
    REDUCE_BUDGET_DRASTIC = "reduce_budget_drastic"
    OPTIMIZE_FOR_CTR = "optimize_for_ctr"
    OPTIMIZE_FOR_REACH = "optimize_for_reach"
    ADJUST_TARGETING_NARROW = "adjust_targeting_narrow"
    ADJUST_TARGETING_BROAD = "adjust_targeting_broad"


class CampaignType(str, Enum):
    """Campaign types"""
    CONVERSION = "conversion"
    AWARENESS = "awareness"
    REACH = "reach"
    ENGAGEMENT = "engagement"
    TRAFFIC = "traffic"


class RiskAppetite(str, Enum):
    """Risk appetite levels"""
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


class Competition(str, Enum):
    """Competition levels"""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


# ============================================================================
# VALUE OBJECTS
# ============================================================================

@dataclass(frozen=True)
class CampaignMetrics:
    """Value object for campaign performance metrics"""
    ctr: float = 2.0  # Click-through rate
    cpm: float = 10.0  # Cost per mille
    cpc: float = 0.5  # Cost per click
    impressions: int = 10000
    clicks: int = 200
    conversions: int = 20
    spend: float = 100.0
    revenue: float = 200.0
    roas: float = 2.0  # Return on ad spend
    budget_utilization: float = 0.8
    reach: int = 8000
    frequency: float = 1.25

    def is_performing_well(self) -> bool:
        """Business Rule: Is this campaign performing well?"""
        return (
            self.roas >= 2.0 and
            self.ctr >= 1.5 and
            self.conversions >= 10
        )

    def needs_optimization(self) -> bool:
        """Business Rule: Does this campaign need optimization?"""
        return (
            self.roas < 1.5 or
            self.ctr < 1.0 or
            self.budget_utilization > 0.9
        )


@dataclass(frozen=True)
class CampaignContext:
    """Value object for campaign context"""
    strategic_context: str
    campaign_type: CampaignType = CampaignType.CONVERSION
    risk_appetite: RiskAppetite = RiskAppetite.MODERATE
    competition: Competition = Competition.MODERATE

    # Advanced context
    time_of_day: str = "business_hours"
    day_of_week: str = "weekday"
    seasonality: str = "normal"
    market_conditions: str = "stable"
    brazil_region: str = "southeast"

    def normalize(self) -> str:
        """Business Rule: Normalize context for Q-table lookup"""
        # Preserve specific contexts for strategy diversity
        if len(self.strategic_context) > 20 and "_" in self.strategic_context:
            return self.strategic_context.upper().replace(" ", "_")

        # Generic mappings for simple contexts
        generic_mappings = {
            "minimize cpa": "MINIMIZE_CPA",
            "maximize roas": "MAXIMIZE_ROAS",
            "brand awareness": "BRAND_AWARENESS",
            "conversions": "MAXIMIZE_CONVERSIONS",
            "reach": "MAXIMIZE_REACH",
            "ctr": "MAXIMIZE_CTR"
        }

        context_lower = self.strategic_context.lower().strip()
        if context_lower in generic_mappings:
            return generic_mappings[context_lower]

        # Preserve specificity
        return self.strategic_context.upper().replace(" ", "_").replace("-", "_")


# ============================================================================
# ENTITIES
# ============================================================================

@dataclass
class Experience:
    """
    Experience entity - Represents a single learning experience
    Core element of the Q-Learning algorithm
    """
    id: str
    context: str
    action: str
    reward: float  # Range: -1.0 to 1.0
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    processed: bool = False
    processed_at: Optional[datetime] = None

    def mark_processed(self) -> None:
        """Business Rule: Mark experience as processed"""
        self.processed = True
        self.processed_at = datetime.utcnow()

    def is_positive_reward(self) -> bool:
        """Business Rule: Is this a positive learning experience?"""
        return self.reward > 0.0

    def age_minutes(self) -> float:
        """Business Rule: How old is this experience?"""
        age = datetime.utcnow() - self.timestamp
        return age.total_seconds() / 60


@dataclass
class Strategy:
    """
    Strategy entity - Learned strategy for a specific context
    Represents accumulated knowledge about what works
    """
    context: str
    best_action: str
    best_q_value: float
    total_experiences: int = 0
    actions_count: int = 0
    action_details: Dict[str, Dict] = field(default_factory=dict)
    q_values: Dict[str, float] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_updated: datetime = field(default_factory=datetime.utcnow)
    algorithm_version: str = "q_learning_v1"

    def update_with_action(self, action: str, q_value: float, reward: float) -> None:
        """Business Rule: Update strategy with new action result"""
        self.total_experiences += 1
        self.last_updated = datetime.utcnow()

        # Initialize action details if not exists
        if action not in self.action_details:
            self.action_details[action] = {
                "count": 0,
                "total_reward": 0.0,
                "avg_reward": 0.0,
                "q_value": 0.0,
                "last_used": datetime.utcnow().isoformat()
            }

        # Update action details
        detail = self.action_details[action]
        detail["count"] += 1
        detail["total_reward"] += reward
        detail["avg_reward"] = detail["total_reward"] / detail["count"]
        detail["q_value"] = q_value
        detail["last_used"] = datetime.utcnow().isoformat()

        # Update Q-values
        self.q_values[action] = q_value

        # Update best action if needed
        if q_value > self.best_q_value:
            self.best_action = action
            self.best_q_value = q_value

        self.actions_count = len(self.action_details)

    def get_confidence(self) -> float:
        """Business Rule: Calculate confidence based on experience"""
        # More experiences = higher confidence, capped at 0.95
        return min(0.95, 0.3 + (self.total_experiences * 0.02))

    def should_explore(self, exploration_rate: float) -> bool:
        """Business Rule: Should we explore vs exploit?"""
        import random
        return random.random() < exploration_rate


@dataclass
class QTable:
    """
    Q-Table entity - Core of the Q-Learning algorithm
    Maps (context, action) pairs to Q-values
    """
    table: Dict[str, Dict[str, float]] = field(default_factory=dict)
    learning_rate: float = 0.1
    discount_factor: float = 0.95

    def get_q_value(self, context: str, action: str) -> float:
        """Get Q-value for a (context, action) pair"""
        if context not in self.table:
            return 0.0
        return self.table[context].get(action, 0.0)

    def update_q_value(self, context: str, action: str, reward: float) -> float:
        """
        Business Rule: Q-Learning Update Formula
        Q(s,a) = Q(s,a) + α * [R + γ * max(Q(s',a')) - Q(s,a)]
        """
        # Initialize if needed
        if context not in self.table:
            self.table[context] = {}
        if action not in self.table[context]:
            self.table[context][action] = 0.0

        # Q-Learning formula
        old_q = self.table[context][action]
        max_future_q = max(self.table[context].values()) if self.table[context] else 0.0
        new_q = old_q + self.learning_rate * (reward + self.discount_factor * max_future_q - old_q)

        self.table[context][action] = new_q
        return new_q

    def get_best_action(self, context: str, available_actions: List[str]) -> Optional[str]:
        """Business Rule: Get best action for a context (exploitation)"""
        if context not in self.table or not self.table[context]:
            return None

        # Filter to available actions only
        valid_actions = {
            action: q_value
            for action, q_value in self.table[context].items()
            if action in available_actions
        }

        if not valid_actions:
            return None

        return max(valid_actions, key=valid_actions.get)

    def get_random_action(self, available_actions: List[str]) -> str:
        """Business Rule: Get random action (exploration)"""
        import random
        return random.choice(available_actions)


@dataclass
class DualBuffer:
    """
    Dual Buffer entity - Manages active and historical experiences
    Active buffer: For real-time learning
    History buffer: For observability and long-term analysis
    """
    active_buffer: List[Experience] = field(default_factory=list)
    history_buffer: List[Experience] = field(default_factory=list)
    max_active_size: int = 25
    max_history_size: int = 1000
    auto_process_threshold: int = 15
    history_retention_hours: int = 72

    def add_experience(self, experience: Experience) -> bool:
        """Business Rule: Add experience to active buffer"""
        self.active_buffer.append(experience)

        # Check if we need to move overflow to history
        if len(self.active_buffer) > self.max_active_size:
            overflow_count = len(self.active_buffer) - self.max_active_size
            experiences_to_move = self.active_buffer[:overflow_count]

            for exp in experiences_to_move:
                self.history_buffer.append(exp)

            self.active_buffer = self.active_buffer[overflow_count:]
            return True

        return False

    def should_auto_process(self) -> bool:
        """Business Rule: Should we automatically process experiences?"""
        return len(self.active_buffer) >= self.auto_process_threshold

    def get_unprocessed_experiences(self) -> List[Experience]:
        """Get all unprocessed experiences from active buffer"""
        return [exp for exp in self.active_buffer if not exp.processed]

    def move_to_history(self, experiences: List[Experience]) -> None:
        """Business Rule: Move processed experiences to history"""
        for exp in experiences:
            exp.mark_processed()
            self.history_buffer.append(exp)
            if exp in self.active_buffer:
                self.active_buffer.remove(exp)

        # Cleanup old history
        self._cleanup_old_history()

    def _cleanup_old_history(self) -> int:
        """Business Rule: Remove old experiences from history"""
        cutoff_time = datetime.utcnow() - timedelta(hours=self.history_retention_hours)
        original_count = len(self.history_buffer)

        # Filter by retention time
        self.history_buffer = [
            exp for exp in self.history_buffer
            if exp.timestamp >= cutoff_time
        ]

        # Apply max size limit (keep most recent)
        if len(self.history_buffer) > self.max_history_size:
            self.history_buffer = sorted(
                self.history_buffer,
                key=lambda x: x.timestamp,
                reverse=True
            )[:self.max_history_size]

        return original_count - len(self.history_buffer)

    def get_active_buffer_utilization(self) -> float:
        """Get active buffer utilization percentage"""
        if self.max_active_size == 0:
            return 0.0
        return (len(self.active_buffer) / self.max_active_size) * 100

    def get_history_buffer_utilization(self) -> float:
        """Get history buffer utilization percentage"""
        if self.max_history_size == 0:
            return 0.0
        return (len(self.history_buffer) / self.max_history_size) * 100


# ============================================================================
# DOMAIN EXCEPTIONS
# ============================================================================

class RLDomainException(Exception):
    """Base exception for RL domain"""
    pass


class InvalidRewardException(RLDomainException):
    """Reward value is invalid"""
    pass


class InvalidContextException(RLDomainException):
    """Context is invalid"""
    pass


class InvalidActionException(RLDomainException):
    """Action is invalid"""
    pass
