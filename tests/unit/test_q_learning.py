"""
Unit Tests - Q-Learning Algorithm
Tests for RL Engine Q-Learning implementation
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock
import sys

sys.path.insert(0, '/home/user/Apex-System/src')
sys.path.insert(0, '/home/user/Apex-System/src/services/rl_engine')

from services.rl_engine.domain.models import (
    ActionType,
    CampaignType,
    RiskAppetite,
    Competition,
    CampaignMetrics,
    CampaignContext,
    Experience,
    Strategy,
    QTable,
    DualBuffer,
    InvalidRewardException,
    InvalidContextException,
    InvalidActionException
)
from services.rl_engine.domain.q_learning import QLearningEngine


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def q_learning_engine():
    """Q-Learning engine instance"""
    return QLearningEngine(
        learning_rate=0.1,
        discount_factor=0.95,
        exploration_rate=0.15,
        max_active_buffer=25,
        max_history_buffer=1000,
        auto_process_threshold=15,
        history_retention_hours=72
    )


@pytest.fixture
def sample_context():
    """Sample campaign context"""
    return CampaignContext(
        strategic_context="MAXIMIZE_ROAS",
        campaign_type=CampaignType.CONVERSION,
        risk_appetite=RiskAppetite.MODERATE,
        competition=Competition.MODERATE
    )


@pytest.fixture
def sample_metrics():
    """Sample campaign metrics"""
    return CampaignMetrics(
        ctr=2.5,
        cpm=10.0,
        cpc=0.5,
        impressions=10000,
        clicks=250,
        conversions=25,
        spend=125.0,
        revenue=300.0,
        roas=2.4,
        budget_utilization=0.8,
        reach=8000,
        frequency=1.25
    )


# ============================================================================
# TEST: ADD EXPERIENCE
# ============================================================================

def test_add_experience_valid(q_learning_engine):
    """Test adding a valid experience"""
    # Execute
    experience = q_learning_engine.add_experience(
        context="MAXIMIZE_ROAS",
        action=ActionType.FOCUS_HIGH_VALUE_AUDIENCES.value,
        reward=0.8,
        metadata={"campaign_id": "test_123"}
    )

    # Verify
    assert experience is not None
    assert experience.context == "MAXIMIZE_ROAS"
    assert experience.action == ActionType.FOCUS_HIGH_VALUE_AUDIENCES.value
    assert experience.reward == 0.8
    assert experience.metadata["campaign_id"] == "test_123"
    assert not experience.processed

    # Verify added to buffer
    assert len(q_learning_engine.dual_buffer.active_buffer) == 1


def test_add_experience_invalid_reward(q_learning_engine):
    """Test adding experience with invalid reward"""
    # Reward > 1.0
    with pytest.raises(InvalidRewardException):
        q_learning_engine.add_experience(
            context="MAXIMIZE_ROAS",
            action=ActionType.OPTIMIZE_BIDDING_STRATEGY.value,
            reward=1.5  # Invalid
        )

    # Reward < -1.0
    with pytest.raises(InvalidRewardException):
        q_learning_engine.add_experience(
            context="MAXIMIZE_ROAS",
            action=ActionType.OPTIMIZE_BIDDING_STRATEGY.value,
            reward=-1.5  # Invalid
        )


def test_add_experience_invalid_context(q_learning_engine):
    """Test adding experience with invalid context"""
    with pytest.raises(InvalidContextException):
        q_learning_engine.add_experience(
            context="",  # Empty context
            action=ActionType.OPTIMIZE_BIDDING_STRATEGY.value,
            reward=0.5
        )


def test_add_experience_invalid_action(q_learning_engine):
    """Test adding experience with invalid action"""
    with pytest.raises(InvalidActionException):
        q_learning_engine.add_experience(
            context="MAXIMIZE_ROAS",
            action="invalid_action",  # Not in available actions
            reward=0.5
        )


def test_add_experience_tracks_rewards(q_learning_engine):
    """Test that rewards are tracked in history"""
    # Add multiple experiences
    for reward in [0.8, 0.5, 0.9, 0.7]:
        q_learning_engine.add_experience(
            context="MAXIMIZE_ROAS",
            action=ActionType.FOCUS_HIGH_VALUE_AUDIENCES.value,
            reward=reward
        )

    # Verify rewards tracked
    assert len(q_learning_engine.reward_history) == 4
    assert 0.8 in q_learning_engine.reward_history
    assert 0.5 in q_learning_engine.reward_history


# ============================================================================
# TEST: PROCESS EXPERIENCES (Q-Learning Algorithm)
# ============================================================================

def test_process_experiences_q_learning_formula(q_learning_engine):
    """Test Q-Learning formula: Q(s,a) = Q(s,a) + α * [R + γ * max(Q(s',a')) - Q(s,a)]"""
    # Add experiences
    q_learning_engine.add_experience(
        context="MAXIMIZE_ROAS",
        action=ActionType.FOCUS_HIGH_VALUE_AUDIENCES.value,
        reward=0.8
    )
    q_learning_engine.add_experience(
        context="MAXIMIZE_ROAS",
        action=ActionType.INCREASE_BID_CONVERSION_KEYWORDS.value,
        reward=0.5
    )

    # Process
    result = q_learning_engine.process_experiences()

    # Verify processing
    assert result["processed_count"] == 2
    assert result["strategies_created"] == 1  # One context
    assert result["strategies_updated"] == 0

    # Verify Q-values calculated
    assert "MAXIMIZE_ROAS" in q_learning_engine.q_table.table
    q_values = q_learning_engine.q_table.table["MAXIMIZE_ROAS"]

    # Q-value for focus_high_value_audiences should be higher (better reward)
    assert ActionType.FOCUS_HIGH_VALUE_AUDIENCES.value in q_values
    assert ActionType.INCREASE_BID_CONVERSION_KEYWORDS.value in q_values
    assert q_values[ActionType.FOCUS_HIGH_VALUE_AUDIENCES.value] > q_values[ActionType.INCREASE_BID_CONVERSION_KEYWORDS.value]


def test_process_experiences_creates_strategy(q_learning_engine):
    """Test that processing creates strategies"""
    # Add experience
    q_learning_engine.add_experience(
        context="MAXIMIZE_ROAS",
        action=ActionType.FOCUS_HIGH_VALUE_AUDIENCES.value,
        reward=0.8
    )

    # Process
    result = q_learning_engine.process_experiences()

    # Verify strategy created
    assert result["strategies_created"] == 1
    assert "MAXIMIZE_ROAS" in q_learning_engine.strategies

    strategy = q_learning_engine.strategies["MAXIMIZE_ROAS"]
    assert strategy.context == "MAXIMIZE_ROAS"
    assert strategy.best_action == ActionType.FOCUS_HIGH_VALUE_AUDIENCES.value
    assert strategy.total_experiences == 1


def test_process_experiences_updates_existing_strategy(q_learning_engine):
    """Test that processing updates existing strategies"""
    # Add first experience and process
    q_learning_engine.add_experience(
        context="MAXIMIZE_ROAS",
        action=ActionType.FOCUS_HIGH_VALUE_AUDIENCES.value,
        reward=0.8
    )
    q_learning_engine.process_experiences()

    # Add second experience and process
    q_learning_engine.add_experience(
        context="MAXIMIZE_ROAS",
        action=ActionType.INCREASE_BID_CONVERSION_KEYWORDS.value,
        reward=0.9  # Higher reward
    )
    result = q_learning_engine.process_experiences()

    # Verify strategy updated
    assert result["strategies_created"] == 0
    assert result["strategies_updated"] == 1

    strategy = q_learning_engine.strategies["MAXIMIZE_ROAS"]
    assert strategy.total_experiences == 2
    assert strategy.actions_count == 2  # Two different actions tried


def test_process_experiences_moves_to_history(q_learning_engine):
    """Test that processed experiences move to history"""
    # Add experiences
    for i in range(5):
        q_learning_engine.add_experience(
            context="MAXIMIZE_ROAS",
            action=ActionType.FOCUS_HIGH_VALUE_AUDIENCES.value,
            reward=0.7
        )

    # Verify in active buffer
    assert len(q_learning_engine.dual_buffer.active_buffer) == 5
    assert len(q_learning_engine.dual_buffer.history_buffer) == 0

    # Process
    q_learning_engine.process_experiences()

    # Verify moved to history
    assert len(q_learning_engine.dual_buffer.active_buffer) == 0
    assert len(q_learning_engine.dual_buffer.history_buffer) == 5

    # Verify all marked as processed
    for exp in q_learning_engine.dual_buffer.history_buffer:
        assert exp.processed
        assert exp.processed_at is not None


def test_process_experiences_empty_buffer(q_learning_engine):
    """Test processing with empty buffer"""
    # Process with no experiences
    result = q_learning_engine.process_experiences()

    # Verify
    assert result["processed_count"] == 0
    assert result["strategies_created"] == 0


# ============================================================================
# TEST: GENERATE ACTION (Epsilon-Greedy)
# ============================================================================

def test_generate_action_with_learned_strategy(q_learning_engine, sample_context, sample_metrics):
    """Test generating action with a learned strategy"""
    # Setup - add and process experiences to create strategy
    for _ in range(20):
        q_learning_engine.add_experience(
            context="MAXIMIZE_ROAS",
            action=ActionType.FOCUS_HIGH_VALUE_AUDIENCES.value,
            reward=0.8
        )
    q_learning_engine.process_experiences()

    # Generate action
    action, confidence, reasoning = q_learning_engine.generate_action(
        sample_context,
        sample_metrics
    )

    # Verify
    assert action is not None
    assert action in [act.value for act in ActionType]
    assert 0.0 <= confidence <= 1.0
    assert reasoning is not None
    assert len(reasoning) > 0


def test_generate_action_epsilon_greedy_exploration(q_learning_engine, sample_context, sample_metrics):
    """Test epsilon-greedy exploration vs exploitation"""
    # Setup - create a strong strategy
    for _ in range(50):
        q_learning_engine.add_experience(
            context="MAXIMIZE_ROAS",
            action=ActionType.FOCUS_HIGH_VALUE_AUDIENCES.value,
            reward=0.9
        )
    q_learning_engine.process_experiences()

    # Generate many actions
    actions = []
    for _ in range(100):
        action, confidence, reasoning = q_learning_engine.generate_action(
            sample_context,
            sample_metrics
        )
        actions.append(action)

    # With exploration_rate=0.15, we should see some variety
    # Not all actions should be the same (some exploration)
    unique_actions = set(actions)
    assert len(unique_actions) > 1  # Should have explored at least once


def test_generate_action_heuristic_fallback(q_learning_engine, sample_metrics):
    """Test heuristic fallback for unknown context"""
    # Context without any learned strategy
    unknown_context = CampaignContext(
        strategic_context="MINIMIZE_CPA",
        campaign_type=CampaignType.CONVERSION,
        risk_appetite=RiskAppetite.CONSERVATIVE,
        competition=Competition.HIGH
    )

    # Generate action
    action, confidence, reasoning = q_learning_engine.generate_action(
        unknown_context,
        sample_metrics
    )

    # Verify heuristic was used
    assert action is not None
    assert confidence == 0.5  # Heuristic confidence
    assert "Heuristic" in reasoning


def test_generate_action_tracks_metrics(q_learning_engine, sample_context, sample_metrics):
    """Test that action generation tracks metrics"""
    # Initial state
    initial_actions = q_learning_engine.total_actions

    # Generate action
    q_learning_engine.generate_action(sample_context, sample_metrics)

    # Verify metrics updated
    assert q_learning_engine.total_actions == initial_actions + 1
    assert len(q_learning_engine.confidence_history) > 0


# ============================================================================
# TEST: DUAL BUFFER
# ============================================================================

def test_dual_buffer_auto_process_threshold(q_learning_engine):
    """Test dual buffer auto-processes at threshold"""
    # Add experiences below threshold
    for i in range(14):
        q_learning_engine.add_experience(
            context="MAXIMIZE_ROAS",
            action=ActionType.OPTIMIZE_BIDDING_STRATEGY.value,
            reward=0.5
        )

    # Should NOT auto-process yet
    assert not q_learning_engine.should_process_experiences()
    assert len(q_learning_engine.dual_buffer.active_buffer) == 14

    # Add one more to hit threshold (15)
    q_learning_engine.add_experience(
        context="MAXIMIZE_ROAS",
        action=ActionType.OPTIMIZE_BIDDING_STRATEGY.value,
        reward=0.5
    )

    # Should auto-process now
    assert q_learning_engine.should_process_experiences()


def test_dual_buffer_overflow_to_history(q_learning_engine):
    """Test buffer overflow moves experiences to history"""
    # Add more than max_active_buffer (25)
    for i in range(30):
        q_learning_engine.add_experience(
            context="MAXIMIZE_ROAS",
            action=ActionType.OPTIMIZE_BIDDING_STRATEGY.value,
            reward=0.5
        )

    # Verify overflow
    assert len(q_learning_engine.dual_buffer.active_buffer) <= 25
    assert len(q_learning_engine.dual_buffer.history_buffer) > 0


def test_dual_buffer_history_cleanup(q_learning_engine):
    """Test history buffer cleanup of old experiences"""
    # Add old experiences to history
    dual_buffer = q_learning_engine.dual_buffer

    # Create old experience
    old_experience = Experience(
        id="old_1",
        context="TEST",
        action="test_action",
        reward=0.5,
        timestamp=datetime.utcnow() - timedelta(hours=100),  # Old
        processed=True
    )
    dual_buffer.history_buffer.append(old_experience)

    # Create recent experience
    recent_experience = Experience(
        id="recent_1",
        context="TEST",
        action="test_action",
        reward=0.5,
        timestamp=datetime.utcnow(),  # Recent
        processed=True
    )
    dual_buffer.history_buffer.append(recent_experience)

    # Cleanup (retention is 72 hours)
    removed = dual_buffer._cleanup_old_history()

    # Verify old removed, recent kept
    assert removed == 1
    assert len(dual_buffer.history_buffer) == 1
    assert dual_buffer.history_buffer[0].id == "recent_1"


# ============================================================================
# TEST: Q-TABLE
# ============================================================================

def test_q_table_update_formula():
    """Test Q-Table update formula"""
    q_table = QTable(learning_rate=0.1, discount_factor=0.95)

    # Initial update (Q-value starts at 0)
    new_q = q_table.update_q_value(
        context="TEST_CONTEXT",
        action="test_action",
        reward=0.8
    )

    # Q(s,a) = 0 + 0.1 * [0.8 + 0.95 * 0 - 0] = 0.08
    assert abs(new_q - 0.08) < 0.001

    # Second update with higher reward
    new_q2 = q_table.update_q_value(
        context="TEST_CONTEXT",
        action="test_action",
        reward=0.9
    )

    # Q-value should increase
    assert new_q2 > new_q


def test_q_table_get_best_action():
    """Test getting best action from Q-table"""
    q_table = QTable()

    # Setup Q-values
    q_table.table["TEST"] = {
        "action_a": 0.5,
        "action_b": 0.8,  # Best
        "action_c": 0.3
    }

    # Get best action
    best = q_table.get_best_action("TEST", ["action_a", "action_b", "action_c"])
    assert best == "action_b"


def test_q_table_get_random_action():
    """Test getting random action"""
    q_table = QTable()
    available_actions = ["action_a", "action_b", "action_c"]

    # Get random action
    action = q_table.get_random_action(available_actions)

    # Verify it's one of the available actions
    assert action in available_actions


# ============================================================================
# TEST: STRATEGY
# ============================================================================

def test_strategy_update_with_action():
    """Test strategy update with action"""
    strategy = Strategy(
        context="TEST_CONTEXT",
        best_action="initial_action",
        best_q_value=0.5
    )

    # Update with better action
    strategy.update_with_action(
        action="better_action",
        q_value=0.8,
        reward=0.7
    )

    # Verify update
    assert strategy.best_action == "better_action"
    assert strategy.best_q_value == 0.8
    assert strategy.total_experiences == 1
    assert "better_action" in strategy.action_details


def test_strategy_confidence_increases_with_experience():
    """Test that confidence increases with more experiences"""
    strategy = Strategy(
        context="TEST",
        best_action="action",
        best_q_value=0.5
    )

    # Initial confidence
    initial_confidence = strategy.get_confidence()

    # Add more experiences
    for i in range(20):
        strategy.total_experiences += 1

    # Confidence should increase
    new_confidence = strategy.get_confidence()
    assert new_confidence > initial_confidence


# ============================================================================
# TEST: CAMPAIGN METRICS
# ============================================================================

def test_campaign_metrics_is_performing_well():
    """Test CampaignMetrics.is_performing_well()"""
    # Good performance
    good_metrics = CampaignMetrics(
        ctr=2.5,
        roas=3.0,
        conversions=25
    )
    assert good_metrics.is_performing_well()

    # Poor performance
    poor_metrics = CampaignMetrics(
        ctr=0.5,
        roas=0.8,
        conversions=5
    )
    assert not poor_metrics.is_performing_well()


def test_campaign_metrics_needs_optimization():
    """Test CampaignMetrics.needs_optimization()"""
    # Needs optimization
    needs_opt = CampaignMetrics(
        ctr=0.8,
        roas=1.2,
        budget_utilization=0.95
    )
    assert needs_opt.needs_optimization()

    # Doesn't need optimization
    good_metrics = CampaignMetrics(
        ctr=2.5,
        roas=3.0,
        budget_utilization=0.7
    )
    assert not good_metrics.needs_optimization()


# ============================================================================
# TEST: CAMPAIGN CONTEXT
# ============================================================================

def test_campaign_context_normalize():
    """Test CampaignContext.normalize()"""
    # Generic context
    context1 = CampaignContext(
        strategic_context="maximize roas",
        campaign_type=CampaignType.CONVERSION
    )
    assert context1.normalize() == "MAXIMIZE_ROAS"

    # Specific context (should preserve)
    context2 = CampaignContext(
        strategic_context="MAXIMIZE_ROAS_ECOMMERCE_TECH_AGGRESSIVE_RISK_0001",
        campaign_type=CampaignType.CONVERSION
    )
    normalized = context2.normalize()
    assert "MAXIMIZE_ROAS_ECOMMERCE_TECH" in normalized


# ============================================================================
# TEST: LEARNING METRICS
# ============================================================================

def test_get_learning_metrics(q_learning_engine):
    """Test getting learning metrics"""
    # Add and process some experiences
    for i in range(10):
        q_learning_engine.add_experience(
            context="MAXIMIZE_ROAS",
            action=ActionType.FOCUS_HIGH_VALUE_AUDIENCES.value,
            reward=0.8
        )
    q_learning_engine.process_experiences()

    # Get metrics
    metrics = q_learning_engine.get_learning_metrics()

    # Verify metrics structure
    assert "total_actions" in metrics
    assert "total_learning_sessions" in metrics
    assert "total_experiences_processed" in metrics
    assert "total_strategies" in metrics
    assert "avg_confidence" in metrics
    assert "avg_reward" in metrics
    assert "avg_q_value" in metrics
    assert "dual_buffer_metrics" in metrics
    assert "hyperparameters" in metrics

    # Verify values
    assert metrics["total_experiences_processed"] == 10
    assert metrics["total_strategies"] == 1
    assert metrics["total_learning_sessions"] == 1


# ============================================================================
# TEST: LOAD/SAVE
# ============================================================================

def test_load_strategies(q_learning_engine):
    """Test loading strategies"""
    # Mock strategy data
    strategies_data = {
        "MAXIMIZE_ROAS": {
            "context": "MAXIMIZE_ROAS",
            "best_action": "focus_high_value_audiences",
            "best_q_value": 0.85,
            "total_experiences": 50,
            "actions_count": 3,
            "action_details": {},
            "q_values": {"focus_high_value_audiences": 0.85},
            "algorithm_version": "q_learning_v1"
        }
    }

    # Load
    q_learning_engine.load_strategies(strategies_data)

    # Verify
    assert "MAXIMIZE_ROAS" in q_learning_engine.strategies
    strategy = q_learning_engine.strategies["MAXIMIZE_ROAS"]
    assert strategy.best_action == "focus_high_value_audiences"
    assert strategy.total_experiences == 50


def test_load_q_table(q_learning_engine):
    """Test loading Q-table"""
    # Mock Q-table data
    q_table_data = {
        "MAXIMIZE_ROAS": {
            "focus_high_value_audiences": 0.85,
            "optimize_bidding_strategy": 0.70
        }
    }

    # Load
    q_learning_engine.load_q_table(q_table_data)

    # Verify
    assert "MAXIMIZE_ROAS" in q_learning_engine.q_table.table
    assert q_learning_engine.q_table.get_q_value("MAXIMIZE_ROAS", "focus_high_value_audiences") == 0.85


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
