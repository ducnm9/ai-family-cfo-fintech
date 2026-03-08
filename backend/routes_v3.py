"""V3 API routes — Life planning, goals, assets, decisions, strategy, AI memory."""

from fastapi import APIRouter, Depends

from models.financial import HouseholdProfile
from models.v3 import (
    LifeEventInput, LifeEventRequest, GoalListRequest, FinancialGoal,
    NetWorthInput, DecisionRequest, DecisionFullRequest, MemoryEntry,
)
from auth.security import get_current_user_id

from life_planning.life_event_engine import simulate_life_event
from goals.goal_optimizer import optimize_goals
from assets.networth_engine import compute_net_worth
from decision.decision_engine import evaluate_decision
from strategy.strategy_engine import recommend_strategy
from memory.ai_memory import (
    store_memory, retrieve_memories, delete_memory,
    store_recommendation_memory,
)

v3_router = APIRouter(prefix="/api/v3", tags=["v3-planning"])


# ---------- Life Planning ----------

@v3_router.post("/life-event")
def life_event(req: LifeEventRequest):
    return simulate_life_event(req.profile, req.event)


# ---------- Goal Optimizer ----------

@v3_router.post("/goals/optimize")
def goals_optimize(request: GoalListRequest):
    return optimize_goals(request)


# ---------- Net Worth ----------

@v3_router.post("/net-worth")
def net_worth(input: NetWorthInput):
    return compute_net_worth(input)


# ---------- Decision Engine ----------

@v3_router.post("/decision")
def decision(req: DecisionFullRequest):
    return evaluate_decision(req.profile, req.request)


# ---------- Strategy ----------

@v3_router.post("/strategy")
def strategy(profile: HouseholdProfile):
    return recommend_strategy(profile)


# ---------- AI Memory ----------

@v3_router.post("/memory")
def add_memory(
    entry: MemoryEntry,
    user_id: int = Depends(get_current_user_id),
):
    return store_memory(user_id, entry.category, entry.content, entry.metadata)


@v3_router.get("/memory")
def get_memories(
    category: str = None,
    limit: int = 20,
    user_id: int = Depends(get_current_user_id),
):
    return retrieve_memories(user_id, category, limit)


@v3_router.delete("/memory/{memory_id}")
def remove_memory(
    memory_id: int,
    user_id: int = Depends(get_current_user_id),
):
    return delete_memory(user_id, memory_id)
