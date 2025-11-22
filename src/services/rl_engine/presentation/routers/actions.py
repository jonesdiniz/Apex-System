"""
RL Engine - Presentation Layer - Actions Router
HTTP endpoints for generating actions
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import uuid

from application.rl_service import RLService
from presentation.dependencies import get_rl_service


router = APIRouter(prefix="/api/v1/actions", tags=["Actions"])


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class CurrentState(BaseModel):
    """Request model for current campaign state"""
    strategic_context: str = Field(..., description="Strategic goal (e.g., 'MAXIMIZE_ROAS')")
    campaign_type: str = Field(default="conversion", description="Campaign type")
    risk_appetite: str = Field(default="moderate", pattern="^(conservative|moderate|aggressive)$")
    competition: str = Field(default="moderate", pattern="^(low|moderate|high)$")

    # Metrics
    ctr: float = Field(default=2.0, ge=0.0, le=100.0, description="Click-through rate")
    cpm: float = Field(default=10.0, ge=0.0, description="Cost per mille")
    cpc: float = Field(default=0.5, ge=0.0, description="Cost per click")
    impressions: int = Field(default=10000, ge=0, description="Total impressions")
    clicks: int = Field(default=200, ge=0, description="Total clicks")
    conversions: int = Field(default=20, ge=0, description="Total conversions")
    spend: float = Field(default=100.0, ge=0.0, description="Total spend")
    revenue: float = Field(default=200.0, ge=0.0, description="Total revenue")
    roas: float = Field(default=2.0, ge=0.0, description="Return on ad spend")
    budget_utilization: float = Field(default=0.8, ge=0.0, le=1.0, description="Budget utilization")
    reach: int = Field(default=8000, ge=0, description="Reach")
    frequency: float = Field(default=1.25, ge=0.0, description="Frequency")

    # Advanced context
    time_of_day: str = Field(default="business_hours", pattern="^(early_morning|business_hours|evening|night)$")
    day_of_week: str = Field(default="weekday", pattern="^(weekday|weekend)$")
    seasonality: str = Field(default="normal", pattern="^(low|normal|high|peak)$")
    market_conditions: str = Field(default="stable", pattern="^(volatile|stable|growing|declining)$")
    brazil_region: str = Field(default="southeast", pattern="^(north|northeast|southeast|south|center_west|national)$")


class ActionRequest(BaseModel):
    """Request model for action generation"""
    current_state: CurrentState
    correlation_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None


class ActionResponse(BaseModel):
    """Response model for action generation"""
    action: str
    confidence: float
    reasoning: str
    context: Dict[str, Any]
    metrics: Dict[str, Any]
    timestamp: str
    correlation_id: Optional[str] = None
    dual_buffer_status: Dict[str, Any]


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/generate", response_model=ActionResponse)
async def generate_action(
    request: ActionRequest,
    rl_service: RLService = Depends(get_rl_service)
):
    """
    Generate optimal action for current campaign state

    Uses Q-Learning algorithm to recommend best action based on:
    - Learned strategies from past experiences
    - Current campaign metrics
    - Strategic context and goals

    Returns action recommendation with confidence score and reasoning
    """
    try:
        # Add correlation_id if not provided
        if not request.correlation_id:
            request.correlation_id = str(uuid.uuid4())

        # Generate action
        state = request.current_state
        result = await rl_service.generate_action(
            strategic_context=state.strategic_context,
            campaign_type=state.campaign_type,
            risk_appetite=state.risk_appetite,
            competition=state.competition,
            ctr=state.ctr,
            cpm=state.cpm,
            cpc=state.cpc,
            impressions=state.impressions,
            clicks=state.clicks,
            conversions=state.conversions,
            spend=state.spend,
            revenue=state.revenue,
            roas=state.roas,
            budget_utilization=state.budget_utilization,
            reach=state.reach,
            frequency=state.frequency,
            time_of_day=state.time_of_day,
            day_of_week=state.day_of_week,
            seasonality=state.seasonality,
            market_conditions=state.market_conditions,
            brazil_region=state.brazil_region
        )

        # Add correlation_id
        result["correlation_id"] = request.correlation_id

        return ActionResponse(**result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/available")
async def get_available_actions():
    """
    Get list of all available actions

    Returns all possible actions that the RL Engine can recommend
    """
    from domain.models import ActionType

    actions = [
        {
            "action": action.value,
            "description": action.name.replace("_", " ").title()
        }
        for action in ActionType
    ]

    return {
        "actions": actions,
        "count": len(actions)
    }


@router.get("/best")
async def get_best_action_for_context(
    context: str = Query(..., description="Strategic context"),
    rl_service: RLService = Depends(get_rl_service)
):
    """
    Get best known action for a specific context

    Returns the action with highest Q-value for the given context,
    or None if no strategy has been learned yet
    """
    try:
        # Get RL engine from service
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

        # Get strategy
        strategy = rl_engine.get_strategy(normalized_context)

        if not strategy:
            return {
                "context": context,
                "normalized_context": normalized_context,
                "best_action": None,
                "message": "No strategy learned for this context yet"
            }

        return {
            "context": context,
            "normalized_context": normalized_context,
            "best_action": strategy.best_action,
            "best_q_value": strategy.best_q_value,
            "confidence": strategy.get_confidence(),
            "total_experiences": strategy.total_experiences,
            "actions_count": strategy.actions_count,
            "created_at": strategy.created_at.isoformat(),
            "last_updated": strategy.last_updated.isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
