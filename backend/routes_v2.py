"""V2 API routes — extends V1 without breaking backward compatibility."""

import json
from fastapi import APIRouter, Depends

from models.financial import HouseholdProfile
from auth.security import get_current_user_id
from db.database import get_wrapped_db

from intelligence.risk_engine import assess_risk
from intelligence.forecast_engine import forecast_from_history
from intelligence.behavior_engine import analyze_behavior
from intelligence.resilience_engine import assess_resilience
from intelligence.financial_score import compute_financial_score
from probabilistic.monte_carlo_simulation import run_monte_carlo
from optimization.allocation_optimizer import optimize_allocation
from advisor.recommendation_engine import generate_v2_recommendations
from simulation.timeline_engine import generate_timelines

v2_router = APIRouter(prefix="/api/v2", tags=["v2-intelligence"])


# ---------- Intelligence endpoints ----------

@v2_router.post("/financial-risk")
def financial_risk(profile: HouseholdProfile):
    return assess_risk(profile)


@v2_router.post("/financial-resilience")
def financial_resilience(profile: HouseholdProfile):
    return assess_resilience(profile)


@v2_router.post("/financial-score")
def financial_score(profile: HouseholdProfile, goal_progress: float = 0):
    return compute_financial_score(profile, goal_progress)


@v2_router.get("/financial-forecast")
def financial_forecast(
    months: int = 12,
    user_id: int = Depends(get_current_user_id),
):
    db = get_wrapped_db()
    rows = db.execute(
        "SELECT month, data, summary FROM monthly_snapshots WHERE user_id = %s ORDER BY month",
        (user_id,),
    ).fetchall()
    db.close()

    snapshots = []
    for r in rows:
        data = r["data"] if isinstance(r["data"], dict) else json.loads(r["data"])
        summary = r["summary"] if isinstance(r["summary"], dict) else json.loads(r["summary"])
        snapshots.append({"month": r["month"], "data": data, "summary": summary})

    return forecast_from_history(snapshots, months)


@v2_router.get("/financial-behavior")
def financial_behavior(user_id: int = Depends(get_current_user_id)):
    db = get_wrapped_db()
    rows = db.execute(
        "SELECT month, data, summary FROM monthly_snapshots WHERE user_id = %s ORDER BY month",
        (user_id,),
    ).fetchall()
    db.close()

    snapshots = []
    for r in rows:
        data = r["data"] if isinstance(r["data"], dict) else json.loads(r["data"])
        summary = r["summary"] if isinstance(r["summary"], dict) else json.loads(r["summary"])
        snapshots.append({"month": r["month"], "data": data, "summary": summary})

    return analyze_behavior(snapshots)


# ---------- Probabilistic ----------

@v2_router.post("/monte-carlo")
def monte_carlo(
    profile: HouseholdProfile,
    simulations: int = 1000,
    months: int = 60,
    income_volatility: float = 0.10,
    expense_volatility: float = 0.15,
):
    return run_monte_carlo(
        profile,
        num_simulations=min(simulations, 5000),  # cap at 5000
        months=min(months, 120),  # cap at 10 years
        income_volatility=income_volatility,
        expense_volatility=expense_volatility,
    )


# ---------- Optimization ----------

@v2_router.post("/optimize-allocation")
def optimize(profile: HouseholdProfile):
    return optimize_allocation(profile)


# ---------- Timelines ----------

@v2_router.post("/timelines")
def timelines(profile: HouseholdProfile, months: int = 60):
    return generate_timelines(profile, min(months, 120))


# ---------- V2 Recommendations (integrates all engines) ----------

@v2_router.post("/recommendations")
def v2_recommendations(profile: HouseholdProfile):
    return generate_v2_recommendations(profile)
