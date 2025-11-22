"""
RL Engine - Presentation Layer - Learning Router
HTTP endpoints for learning from experiences and managing strategies
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import uuid

from application.rl_service import RLService
from presentation.dependencies import get_rl_service


router = APIRouter(prefix="/api/v1", tags=["Learning"])


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class LearnRequest(BaseModel):
    """Request model for learning from experience"""
    context: str = Field(..., description="Strategic context")
    action: str = Field(..., description="Action taken")
    reward: float = Field(..., ge=-1.0, le=1.0, description="Reward received")
    metadata: Optional[Dict[str, Any]] = None
    correlation_id: Optional[str] = None


class BufferStatusResponse(BaseModel):
    """Response model for buffer status"""
    buffer_type: str
    size: int
    max_size: int
    utilization_percent: float
    oldest_entry: Optional[str] = None
    newest_entry: Optional[str] = None
    last_processed: Optional[str] = None


# ============================================================================
# LEARNING ENDPOINTS
# ============================================================================

@router.post("/learn")
async def learn_experience(
    request: LearnRequest,
    rl_service: RLService = Depends(get_rl_service)
):
    """
    Learn from a single experience

    Adds experience to the active buffer. When buffer reaches threshold,
    automatically processes experiences using Q-Learning algorithm.

    **Reward Guidelines:**
    - +1.0: Excellent performance
    - +0.5: Good performance
    - 0.0: Neutral
    - -0.5: Poor performance
    - -1.0: Terrible performance
    """
    try:
        result = await rl_service.learn_from_experience(
            context=request.context,
            action=request.action,
            reward=request.reward,
            metadata=request.metadata,
            correlation_id=request.correlation_id
        )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/force_process")
async def force_process_experiences(
    rl_service: RLService = Depends(get_rl_service)
):
    """
    Force immediate processing of all unprocessed experiences

    Manually trigger Q-Learning update without waiting for auto-threshold.
    Useful for batch processing or manual training sessions.
    """
    try:
        result = await rl_service.process_experiences()
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# STRATEGY ENDPOINTS
# ============================================================================

@router.get("/strategies")
async def get_strategies(
    rl_service: RLService = Depends(get_rl_service)
):
    """
    Get all learned strategies

    Returns complete catalog of learned strategies with Q-values,
    action details, and experience counts.
    """
    try:
        result = await rl_service.get_strategies()
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/strategies/{context}")
async def get_strategy_by_context(
    context: str,
    rl_service: RLService = Depends(get_rl_service)
):
    """
    Get learned strategy for a specific context

    Returns strategy details including:
    - Best action and Q-value
    - All tried actions with performance
    - Total experiences
    - Confidence score
    """
    try:
        rl_engine = rl_service.rl_engine

        # Normalize context
        from domain.models import CampaignContext, CampaignType, RiskAppetite, Competition
        campaign_context = CampaignContext(
            strategic_context=context,
            campaign_type=CampaignType.CONVERSION,
            risk_appetite=RiskAppetite.MODERATE,
            competition=Competition.MODERATE
        )
        normalized_context = campaign_context.normalize()

        strategy = rl_engine.get_strategy(normalized_context)

        if not strategy:
            raise HTTPException(
                status_code=404,
                detail=f"No strategy found for context: {context}"
            )

        return {
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

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# BUFFER ENDPOINTS
# ============================================================================

@router.get("/buffer/active", response_model=Dict[str, Any])
async def get_active_buffer(
    rl_service: RLService = Depends(get_rl_service)
):
    """
    Get active buffer status and contents

    Active buffer contains unprocessed experiences waiting for Q-Learning.
    When buffer reaches threshold, experiences are automatically processed.
    """
    try:
        result = await rl_service.get_buffer_status("active")
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/buffer/history", response_model=Dict[str, Any])
async def get_history_buffer(
    rl_service: RLService = Depends(get_rl_service)
):
    """
    Get history buffer status and contents

    History buffer contains processed experiences for observability.
    Experiences are retained based on retention policy (default 72 hours).
    """
    try:
        result = await rl_service.get_buffer_status("history")
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# METRICS ENDPOINTS
# ============================================================================

@router.get("/metrics")
async def get_metrics(
    rl_service: RLService = Depends(get_rl_service)
):
    """
    Get learning performance metrics

    Returns comprehensive metrics including:
    - Total actions generated
    - Total experiences processed
    - Average confidence, reward, Q-value
    - Buffer utilization
    - Hyperparameters
    """
    try:
        result = await rl_service.get_metrics()
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# CONFIGURATION ENDPOINTS
# ============================================================================

@router.get("/config")
async def get_configuration():
    """
    Get current Q-Learning configuration

    Returns hyperparameters and buffer settings
    """
    from infrastructure.config import get_settings

    settings = get_settings()

    return {
        "hyperparameters": {
            "learning_rate": settings.learning_rate,
            "discount_factor": settings.discount_factor,
            "exploration_rate": settings.exploration_rate,
            "confidence_threshold": settings.confidence_threshold,
            "min_experiences_for_learning": settings.min_experiences_for_learning
        },
        "dual_buffer": {
            "max_active_buffer": settings.max_active_buffer,
            "max_history_buffer": settings.max_history_buffer,
            "auto_process_threshold": settings.auto_process_threshold,
            "history_retention_hours": settings.history_retention_hours
        },
        "performance": {
            "batch_processing_size": settings.batch_processing_size,
            "auto_save_interval": settings.auto_save_interval,
            "memory_cleanup_interval": settings.memory_cleanup_interval
        },
        "service": {
            "service_name": settings.service_name,
            "version": settings.version,
            "environment": settings.environment
        }
    }
